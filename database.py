# Copyright 2024 Killua Zoldyck
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import aiosqlite
import json

class GuildData:
    def __init__(self, guildid, code, groupid, invite, mutedchannelids, code_used, force_mute):
        self.guildid = guildid
        self.code = code
        self.groupid = groupid
        self.invite = invite
        self.mutedchannelids = mutedchannelids
        self.code_used = code_used
        self.force_mute = force_mute

class DummyGuild:
    def __init__(self, guildid):
        self.id = guildid
        
class DummyChannel:
    def __init__(self, guildid, channelid):
        self.id = channelid
        self.guild = Guild(guildid)

class Database:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.db = None 
        self.execute = None 
        self.commit = None 

    async def connect(self):
        """Establish the connection and store the execute/commit functions."""
        self.db = await aiosqlite.connect(self.db_name)
        self.execute = self.db.execute
        self.commit = self.db.commit

    async def close(self):
        """Close the connection if it exists."""
        if self.db:
            await self.db.close()
            self.db = None 

    async def ensure_connected(self):
        """Ensure the connection is established before performing operations."""
        if self.db is None:
            await self.connect()

    async def create_table(self):
        """Create the table if it doesn't exist."""
        await self.ensure_connected()
        query = """
        CREATE TABLE IF NOT EXISTS auth (
            guildid INTEGER UNIQUE,
            code INTEGER DEFAULT NULL,
            tgadmin INTEGER DEFAULT NULL,
            groupid INTEGER DEFAULT NULL,
            invite TEXT DEFAULT NULL,
            mutedchannelids TEXT DEFAULT '[]',
            code_used BOOLEAN DEFAULT FALSE,
            force_mute BOOLEAN DEFAULT FALSE
        );
        """
        await self.execute(query)
        query = """
        CREATE TABLE IF NOT EXISTS privacy (
            userid INTEGER,
            privacy BOOLEAN DEFAULT FALSE
        );
        """
        await self.execute(query)
        query = """
        CREATE TABLE IF NOT EXISTS channels (
            guildid INTEGER UNIQUE,
            chatid INTEGER UNIQUE,
            channel INTEGER DEFAULT NULL
        );
        """
        await self.execute(query)
        query = """
        CREATE TABLE IF NOT EXISTS users (
            guildid INTEGER,
            userid INTEGER,
            muted BOOLEAN DEFAULT FALSE,
            UNIQUE(guildid, userID)
        );
        """
        await self.execute(query)
        await self.commit()

    async def insertGuild(self, guildid: int, code:int = None, groupid: int = None, invite: str = None, mutedchannelids: list = None, code_used: bool = False, force_mute:bool = False):
        """Insert a new guild into the database."""
        await self.ensure_connected()
        if mutedchannelids is None:
            mutedchannelids = []

        mutedchannelids_str = json.dumps(mutedchannelids)
        query = """
        INSERT OR IGNORE INTO auth (guildid, code, groupid, invite, mutedchannelids, code_used, force_mute)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        await self.execute(query, (guildid, code, groupid, invite, mutedchannelids_str, code_used, force_mute))
        await self.commit()
        data = GuildData(guildid, code, groupid, invite, mutedchannelids, code_used, force_mute)
        return data

    async def updateGuild(self, guildid: int, code:int = None, groupid: int = None, invite: str = None, mutedchannelids: list = None, code_used: bool = None, force_mute:bool = None):
        """Update guild information in the database."""
        await self.ensure_connected()
        updates = []
        params = []
        if code is not None:
            updates.append("code = ?")
            params.append(code)
        if groupid is not None:
            updates.append("groupid = ?")
            params.append(groupid)
        if invite is not None:
            updates.append("invite = ?")
            params.append(invite)
        if mutedchannelids is not None:
            updates.append("mutedchannelids = ?")
            params.append(json.dumps(mutedchannelids))
        if code_used is not None:
            updates.append("code_used = ?")
            params.append(code_used)
        if force_mute is not None:
            updates.append("force_mute = ?")
            params.append(force_mute)
        
        if not updates:
            return
        params.append(guildid)
        query = f"UPDATE auth SET {', '.join(updates)} WHERE guildid = ?;"

        await self.execute(query, params)
        await self.commit()

    async def deleteGuild(self, guildid: int):
        """Delete a guild from the database."""
        await self.ensure_connected()
        query = "DELETE FROM auth WHERE guildid = ?;"
        await self.execute(query, (guildid,))
        await self.commit()

    async def getGuild(self, guild):
        """Fetch all users from the database for a given guild."""
        await self.ensure_connected()
        data = None
        query = "SELECT * FROM auth WHERE guildid = ?;"
        async with self.execute(query, (guild.id,)) as cursor:
            result = await cursor.fetchone()
            if result:
                guildid, code, groupid, invite, mutedchannelids, code_used, force_mute = result
                mutedchannelids = json.loads(mutedchannelids)
                data = GuildData(guildid, code, groupid, invite, mutedchannelids, code_used, force_mute)
        return data

    async def insertPrivacy(self, userid, privacy:bool =False):
        """Insert user privacy in the privacy table."""
        await self.ensure_connected()
        query = """
        INSERT OR IGNORE INTO privacy (userid, privacy)
        VALUES (?, ?);
        """
        await self.execute(query, (userid, privacy))
        await self.commit()

    async def updatePrivacy(self, userid, privacy:bool):
        """Update user privacy value in the privacy table."""
        await self.ensure_connected()
        query = f"UPDATE privacy SET privacy = ? WHERE userid = ?;"
        await self.execute(query, (privacy, userid))
        await self.commit()

    async def checkPrivacy(self, userid):
        """Check if the user privacy is enabled or not."""
        await self.ensure_connected()
        query = "SELECT privacy FROM privacy WHERE userid = ?;"
        async with self.execute(query, (userid,)) as cursor:
            row = await cursor.fetchone()
        if not row:
            await self.insertPrivacy(userid, False)
        return row[0] if row else False

    async def insertUser(self, guildid, userid, muted:bool = False):
        """Insert user mute status."""
        await self.ensure_connected()
        query = """
        INSERT OR IGNORE INTO users (guildid, userid, muted)
        VALUES (?, ?, ?);
        """
        await self.execute(query, (guildid, userid, muted))
        await self.commit()

    async def updateUser(self, guildid, userid, muted: bool):
        """Update user mute status."""
        await self.ensure_connected()
        query = f"UPDATE users SET muted = ? WHERE guildid = ? AND userid = ?;"
        await self.execute(query, (muted, guildid, userid))
        await self.commit()

    async def getUser(self, guildid, userid):
        """Get user mute status."""
        await self.ensure_connected()
        query = "SELECT muted FROM users WHERE guildid = ? AND userid = ?;"
        async with self.execute(query, (guildid, userid)) as cursor:
            row = await cursor.fetchone()
        if not row:
            await self.insertUser(guildid, userid)
        return row[0] if row else False

    async def insertActivech(self, guildid:int, chatid:int , channelid:int = None):
        """Insert active channel in channels table."""
        await self.ensure_connected()
        query = """
        INSERT OR IGNORE INTO channels (guildid, chatid, channel)
        VALUES (?, ?, ?);
        """
        await self.execute(query, (guildid, chatid, channelid))
        await self.commit()

    async def updateActivech(self, channelid:int, guildid:int=None, chatid:int=None):
        """Update active channel value in channels table."""
        await self.ensure_connected()
        if guildid:
            query = f"UPDATE channels SET channel = ? WHERE guildid = ?;"
            await self.execute(query, (channelid, guildid))
        elif chatid:
            query = f"UPDATE channels SET channel = ? WHERE chatid = ?;"
            await self.execute(query, (channelid, chatid))
        else:
            return None
        await self.commit()

    async def deleteActivech(self, guildid:int=None, chatid:int=None):
        """Delete a channel from the channels."""
        await self.ensure_connected()
        if guildid:
            query = "DELETE FROM channels WHERE guildid = ?;"
            await self.execute(query, (guildid,))
        elif chatid:
            query = "DELETE FROM channels WHERE chatid = ?;"
            await self.execute(query, (chatid,))
        else:
            return None
        await self.commit()

    async def getActivech(self, guildid:int=None, chatid:int=None):
        """Fetch active channel from channels table."""
        await self.ensure_connected()
        if guildid:
            query = "SELECT channel, chatid FROM channels WHERE guildid = ?;"
            async with self.execute(query, (guildid,)) as cursor:
                row = await cursor.fetchone()
        elif chatid:
            query = "SELECT channel, guildid FROM channels WHERE chatid = ?;"
            async with self.execute(query, (chatid,)) as cursor:
                row = await cursor.fetchone()
        else:
            return None
        return row if row else None
