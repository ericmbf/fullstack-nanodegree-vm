from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Category, Item, User

engine = create_engine('postgresql://catalog:password@localhost/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

user1 = User(username='someone')
session.add(user1)
session.commit()
session.refresh(user1)

category1 = Category(name='Hockey')
session.add(category1)
session.commit()

item1 = Item(name="Stick", description="""A hockey stick is a piece of sport
    equipment used by the players in all the forms of hockey to move the ball
    or puck (as appropriate to the type of hockey).""", category=category1, 
    user_id=user1.id, user=user1)

session.add(item1)
session.commit()

# Insert default categories
session.add(Category(name='Soccer'))
session.add(Category(name='Basketball'))
session.add(Category(name='Baseball'))
session.add(Category(name='Frisbee'))
session.add(Category(name='Snowboarding'))
session.add(Category(name='Rock Climbing'))
session.add(Category(name='Foosball'))
session.add(Category(name='Skating'))
session.commit()

print "Added Categories!"
