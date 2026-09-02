import os
import motor.motor_asyncio
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    raise RuntimeError('MONGO_URI is not set. Add it to your .env / Render environment variables.')


_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
_db = _client['inevitable']
_log_channels = _db['log_channels']


async def get_log_channel(guild_id: int) -> int | None:
    """Returns the log channel ID for a guild, or None if not set."""
    doc = await _log_channels.find_one({'guild_id': guild_id})
    return doc['channel_id'] if doc else None


async def set_log_channel(guild_id: int, channel_id: int) -> None:
    """Saves or updates the log channel for a guild."""
    await _log_channels.update_one(
        {'guild_id': guild_id},
        {'$set': {'channel_id': channel_id}},
        upsert=True
    )


async def remove_log_channel(guild_id: int) -> None:
    """Removes the log channel entry for a guild."""
    await _log_channels.delete_one({'guild_id': guild_id})
