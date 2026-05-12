import discord


class BankErrors:
    class BalanceTooHigh(Exception):
        def __init__(self, max_balance):
            self.max_balance = max_balance


errors = BankErrors()


def humanize_number(val: int) -> str:
    return f"{val:,}"


class BankMock:
    async def get_economy(self, context_obj):
        """Helper to get economy safely from a member or guild."""
        obj = context_obj.guild if getattr(context_obj, "guild", None) else context_obj
        if hasattr(obj, "_state"):
            client = obj._state._get_client()
            return client.get_cog("Economy")
        return None

    async def can_spend(self, member: discord.Member, amount: int) -> bool:
        eco = await self.get_economy(member)
        if not eco:
            return False
        bal = await eco.get_balance(member.id)
        return bal >= amount

    async def get_currency_name(self, guild: discord.Guild) -> str:
        return "Kingshot Bucks"

    async def withdraw_credits(self, member: discord.Member, amount: int):
        eco = await self.get_economy(member)
        if eco:
            success = await eco.remove_balance(member.id, amount)
            if not success:
                raise ValueError("Not enough balance")

    async def deposit_credits(self, member: discord.Member, amount: int):
        eco = await self.get_economy(member)
        if eco:
            new_bal = await eco.add_balance(member.id, amount)
            if isinstance(new_bal, bytes):
                new_bal = int(new_bal)
            if new_bal > 5000000:
                await eco.db.set(f"ks_bucks:{member.id}", "5000000")
                raise errors.BalanceTooHigh(5000000)

    async def set_balance(self, member: discord.Member, amount: int):
        eco = await self.get_economy(member)
        if eco:
            await eco.db.set(f"ks_bucks:{member.id}", str(amount))


bank = BankMock()
