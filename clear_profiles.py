import sys
import os
import asyncio
sys.path.append(os.getcwd())

from app.database.session import AsyncSessionLocal
from app.models.user_profile import UserProfile
from sqlalchemy import delete

async def main():
    async with AsyncSessionLocal() as db:
        await db.execute(delete(UserProfile))
        await db.commit()
        print('Deleted all user profiles')

if __name__ == '__main__':
    asyncio.run(main())
