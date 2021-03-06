import discord
import aiohttp
import json
import util_functions
import os
import redisInterface
from discord.ext import commands

class GameAlerts():

    def __init__(self, bot):
        self.bot = bot
        self.API_KEY = os.environ.get('API_KEY')

    @commands.command(pass_context=True, no_pm=True)
    async def alert(self, ctx, minlevel : int, maxlevel : int):
        """Sends out a notification to all registered players."""
        allowed = False
        for role in ctx.message.author.roles:
            if role.name == "Dungeon Master" or role.name == "Trial DM":
                allowed = True
        if allowed:

            UserData = self.bot.db.from_json(self.bot.db.get_val('UserData'))

            data = {}
            data['users'] = list(UserData.keys())
            data['ids'] = list(UserData.values())

            async with aiohttp.ClientSession() as session:
                async with session.post('https://avrae.io/api/bulkcharacter', 
                    data=json.dumps(data), 
                    headers={"Authorization": self.API_KEY, "Content-Type": "application/json"}) as resp:
                    respData = await resp.json()

            messageTotal = 0
            for userchar, chardata in respData.items():
                if chardata['levels']['level'] <= maxlevel and chardata['levels']['level'] >= minlevel:
                    
                    userID = userchar.split(':')[0]
                    if userID != ctx.message.author.id:
                        messageTotal += 1
                        try:
                            await self.bot.send_message(ctx.message.server.get_member(userID), 
                            "Greetings! {} has announced a game for levels {} through {}! This is a courtesy notification that your currently active character is eligible to sign up!".format(ctx.message.author.display_name, minlevel, maxlevel))      
                        except (discord.Forbidden):
                            del UserData[userID]
                            self.bot.db.set_val('UserData', self.bot.db.to_json(UserData))
                        except (discord.errors.InvalidArgument):
                            pass
        else:
            return await self.bot.say("Apologies, {}, but you do not have the necessary title to request a game alert! If you would like to start the process of becoming a Dungeon Master, please contact a Helper!".format(ctx.message.author.mention))
        await self.bot.say("I have dispatched my messengers, {}. In total, {} notifications have been sent out. I bid you good luck on your session!".format(ctx.message.author.mention, messageTotal))
    
    @commands.command(pass_context=True, hidden=True)
    async def getUsers(self, ctx):
        print(self.bot.db.get_val('UserData'))

    @commands.command(pass_context=True)
    async def register(self, ctx):
        """Saves your currently active character level alerted for DM quests."""
        UserData = self.bot.db.from_json(self.bot.db.get_val('UserData'))
        USERID = ctx.message.author.id
        
        async with aiohttp.ClientSession() as session:
            async with session.get('https://avrae.io/api/activecharacter', params={"user": USERID}, headers={"Authorization": self.API_KEY}) as resp:
                UserData[USERID] = await resp.json()

                self.bot.db.set_val('UserData', self.bot.db.to_json(UserData))
        return await self.bot.say("Certainly, {}. I have updated my records with your currently active character's identity!".format(ctx.message.author.mention))

    @commands.command(pass_context=True)
    async def unregister(self, ctx):
        """Removes your character, so you are no longer alerted for DM quests."""
        UserData = self.bot.db.from_json(self.bot.db.get_val('UserData'))
        
        del UserData[ctx.message.author.id]
        self.bot.db.set_val('UserData', self.bot.db.to_json(UserData))

        return await self.bot.say("Certainly, {}. I have removed you from my records. I am sad to no longer be corresponding with you!".format(ctx.message.author.mention))


def setup(bot):
    bot.add_cog(GameAlerts(bot))
    