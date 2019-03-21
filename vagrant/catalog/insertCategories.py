from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Category, Item

engine = create_engine('postgresql://catalog:password@localhost/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

category1 = Category(name='Hockey')
session.add(category1)
session.commit()

item1 = Item(name="Stick", description="""A hockey stick is a piece of sport
    equipment used by the players in all the forms of hockey to move the ball
    or puck (as appropriate to the type of hockey) either to push, pull, hit,
    strike, flick, steer, launch or stop the ball/puck during play with the
    objective being to move the ball/puck around the playing area and between
    team members using the stick, and to ultimately score a goal with it
    against an opposing team.""", category=category1)

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
