import asyncio
import re
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from data_manager import save_mimic_emojis

DEFAULT_MIMIC_EMOJI = "➕"
WEBHOOK_NAME = "串串串"
DELETE_AFTER_SECONDS = 30 * 60
_CUSTOM_EMOJI = re.compile(r"^<a?:[A-Za-z0-9_]+:\d+>$")


def emoji_matches(emoji_text: str, configured: str) -> bool:
    """Return True when the reaction emoji is the guild's trigger emoji."""
    if not emoji_text or not configured:
        return False
    return emoji_text.strip() == configured.strip()


def normalize_emoji_setting(raw: str) -> str | None:
    """Accept one unicode emoji or a custom emoji token. '+' maps to the default plus."""
    text = (raw or "").strip()
    if not text or any(ch.isspace() for ch in text) or len(text) > 64:
        return None
    if text == "+":
        return DEFAULT_MIMIC_EMOJI
    if _CUSTOM_EMOJI.fullmatch(text):
        return text
    if text.isascii() and text.replace("_", "").isalnum():
        return None
    return text


def sanitize_username(name: str) -> str:
    """Fallback webhook username after Discord rejects the display name."""
    cleaned = name or ""
    cleaned = re.sub(r"discord", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"clyde", "", cleaned, flags=re.IGNORECASE)
    for ch in ("@", "#", ":", "`"):
        cleaned = cleaned.replace(ch, "")
    cleaned = " ".join(cleaned.split()).strip()[:80]
    if not cleaned or cleaned.lower() in {"everyone", "here"}:
        return "User"
    return cleaned


def build_resend_content(content: str | None, sticker_urls: list[str]) -> str:
    """Copy message text and append sticker URLs. Webhooks cannot resend stickers."""
    parts = []
    if content and content.strip():
        parts.append(content)
    for url in sticker_urls:
        if url:
            parts.append(url)
    return "\n".join(parts)[:2000]


class MimicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._webhooks: dict[int, discord.Webhook] = {}
        self._webhook_locks: dict[int, asyncio.Lock] = {}
        self._inflight: set[tuple[int, int, int]] = set()
        self._inflight_lock = asyncio.Lock()
        self._delete_tasks: set[asyncio.Task] = set()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id is None or payload.user_id == self.bot.user.id:
            return
        if payload.member is not None and payload.member.bot:
            return

        configured = self.bot.mimic_emojis.get(str(payload.guild_id), DEFAULT_MIMIC_EMOJI)
        if not emoji_matches(str(payload.emoji), configured):
            return

        key = (payload.channel_id, payload.message_id, payload.user_id)
        async with self._inflight_lock:
            if key in self._inflight:
                return
            self._inflight.add(key)
        try:
            await self._resend(payload)
        except Exception as e:
            print(f"❌ Mimic failed for message {payload.message_id}: {e}")
        finally:
            async with self._inflight_lock:
                self._inflight.discard(key)

    async def _resend(self, payload: discord.RawReactionActionEvent):
        channel = self.bot.get_channel(payload.channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(payload.channel_id)
            except (discord.Forbidden, discord.HTTPException) as e:
                print(f"❌ Mimic could not fetch channel {payload.channel_id}: {e}")
                return

        parent, thread = await self._resolve_destination(channel)
        if parent is None:
            return

        member = await self._reactor(payload)
        if member is None or member.bot:
            return

        me = parent.guild.me if parent.guild is not None else None
        if me is not None and not parent.permissions_for(me).manage_webhooks:
            print(f"❌ Missing Manage Webhooks in #{parent}")
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except (discord.Forbidden, discord.NotFound, discord.HTTPException) as e:
            print(f"❌ Mimic could not fetch message {payload.message_id}: {e}")
            return

        sticker_urls = []
        for sticker in message.stickers:
            url = getattr(sticker, "url", None)
            if url:
                sticker_urls.append(str(url))

        content = build_resend_content(message.content, sticker_urls)
        embeds = [embed for embed in message.embeds if embed.type == "rich"][:10]
        attachments = list(message.attachments[:10])
        if not content and not embeds and not attachments:
            print(f"ℹ️ Mimic skipped empty message {message.id}")
            return

        webhook = await self._get_webhook(parent)
        if webhook is None:
            return

        username = (member.display_name or member.name or "User").strip()[:80] or "User"
        avatar_url = member.display_avatar.replace(size=128).url
        await self._send_via_webhook(
            parent, webhook, thread, content, embeds, attachments, username, avatar_url
        )

    async def _reactor(self, payload: discord.RawReactionActionEvent):
        if payload.member is not None:
            return payload.member
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return None
        member = guild.get_member(payload.user_id)
        if member is not None:
            return member
        try:
            return await guild.fetch_member(payload.user_id)
        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"❌ Mimic could not fetch member {payload.user_id}: {e}")
            return None

    async def _resolve_destination(self, channel):
        if isinstance(channel, discord.Thread):
            parent = channel.parent
            if parent is None and channel.parent_id:
                parent = self.bot.get_channel(channel.parent_id)
                if parent is None:
                    try:
                        parent = await self.bot.fetch_channel(channel.parent_id)
                    except (discord.Forbidden, discord.HTTPException) as e:
                        print(f"❌ Mimic could not fetch thread parent {channel.parent_id}: {e}")
                        return None, None
            if parent is None or not hasattr(parent, "create_webhook"):
                return None, None
            return parent, channel
        if isinstance(channel, discord.TextChannel):
            return channel, None
        return None, None

    def _lock_for(self, channel_id: int) -> asyncio.Lock:
        lock = self._webhook_locks.get(channel_id)
        if lock is None:
            lock = asyncio.Lock()
            self._webhook_locks[channel_id] = lock
        return lock

    async def _get_webhook(self, parent: discord.abc.GuildChannel):
        cached = self._webhooks.get(parent.id)
        if cached is not None:
            return cached

        async with self._lock_for(parent.id):
            cached = self._webhooks.get(parent.id)
            if cached is not None:
                return cached
            try:
                hooks = await parent.webhooks()
            except discord.Forbidden:
                print(f"❌ Missing Manage Webhooks in #{parent}")
                return None
            except discord.HTTPException as e:
                print(f"❌ Mimic could not list webhooks in #{parent}: {e}")
                return None

            hook = discord.utils.find(
                lambda item: item.name == WEBHOOK_NAME and item.user is not None and item.user.id == self.bot.user.id,
                hooks,
            )
            if hook is None:
                try:
                    hook = await parent.create_webhook(name=WEBHOOK_NAME, reason="Emoji mimic resend")
                except discord.Forbidden:
                    print(f"❌ Missing Manage Webhooks in #{parent}")
                    return None
                except discord.HTTPException as e:
                    print(f"❌ Mimic could not create webhook in #{parent}: {e}")
                    return None
            self._webhooks[parent.id] = hook
            return hook

    async def _execute(self, webhook, thread, content, embeds, attachments, username, avatar_url):
        files = [await attachment.to_file() for attachment in attachments]
        kwargs = {
            "content": content or None,
            "username": username,
            "avatar_url": avatar_url,
            "allowed_mentions": discord.AllowedMentions.none(),
            "wait": True,
        }
        if embeds:
            kwargs["embeds"] = embeds
        if files:
            kwargs["files"] = files
        if thread is not None:
            kwargs["thread"] = thread
        return await webhook.send(**kwargs)

    def _schedule_delete(self, webhook, message_id: int, thread):
        task = asyncio.create_task(self._delete_later(webhook, message_id, thread))
        self._delete_tasks.add(task)
        task.add_done_callback(self._delete_tasks.discard)

    async def _delete_later(self, webhook, message_id: int, thread):
        try:
            await asyncio.sleep(DELETE_AFTER_SECONDS)
            if thread is not None:
                await webhook.delete_message(message_id, thread=thread)
            else:
                await webhook.delete_message(message_id)
        except (discord.NotFound, discord.HTTPException) as e:
            print(f"❌ Mimic could not delete message {message_id}: {e}")

    async def _send_via_webhook(self, parent, webhook, thread, content, embeds, attachments, username, avatar_url):
        name = username
        used_fallback = False
        recreated = False
        while True:
            try:
                sent = await self._execute(webhook, thread, content, embeds, attachments, name, avatar_url)
                if sent is not None:
                    self._schedule_delete(webhook, sent.id, thread)
                return
            except discord.NotFound:
                if recreated:
                    print(f"❌ Mimic webhook in #{parent} is missing")
                    return
                self._webhooks.pop(parent.id, None)
                webhook = await self._get_webhook(parent)
                if webhook is None:
                    return
                recreated = True
            except discord.Forbidden as e:
                print(f"❌ Mimic webhook send forbidden in #{parent}: {e}")
                return
            except discord.HTTPException as e:
                if e.status == 400 and not used_fallback:
                    safe = sanitize_username(username)
                    if safe == name:
                        print(f"❌ Mimic webhook rejected the message in #{parent}: {e}")
                        return
                    name = safe
                    used_fallback = True
                    recreated = False
                    continue
                print(f"❌ Mimic webhook send failed in #{parent}: {e}")
                return

    @app_commands.command(name="setmimicemoji", description="Set the emoji that resends a message as the reactor (Admin only)")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(emoji="Unicode emoji or custom emoji, for example ➕")
    async def set_mimic_emoji(self, interaction: discord.Interaction, emoji: str):
        """Set the reaction emoji that copies a message as the reactor."""
        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        normalized = normalize_emoji_setting(emoji)
        if normalized is None:
            await interaction.response.send_message(
                "Please provide a single emoji, such as ➕ or a custom emoji.",
                ephemeral=True,
            )
            return

        try:
            self.bot.mimic_emojis[str(interaction.guild.id)] = normalized
            save_mimic_emojis(self.bot.mimic_emojis)
            embed = discord.Embed(
                title="✅ Mimic Emoji Set",
                description=f"Reacting with {normalized} resends that message using the reactor's name and avatar.",
                color=0x00FF00,
                timestamp=datetime.now(timezone.utc),
            )
            embed.set_footer(text="串串串")
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            print(f"Error in setmimicemoji: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred while setting the emoji.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(MimicCog(bot))
