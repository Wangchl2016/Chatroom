from google.appengine.api import channel
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import db
from google.appengine.ext.webapp.util import login_required
from datetime import datetime

import cgi
import jinja2
import os
import webapp2
import random

DEFAULT_USER_ID = ''
DEFAULT_GROUP_ID = ''

class ChatUser(ndb.Model):
  """ Stored user model. Should be keyed by the User ID. """
  nickname = ndb.StringProperty()

class Friend(ndb.Model):
  nickname = ndb.StringProperty()

def friend_list_key(user_id=DEFAULT_USER_ID):
  """Sub model for representing an author."""
  return ndb.Key('addFriend', user_id)



class ChatGroup(ndb.Model):
  group_name = ndb.StringProperty()
  group_id = ndb.StringProperty()
  token = ndb.StringProperty()

def ChatGroupKey(user_id=DEFAULT_USER_ID):
  """Sub model for representing an author."""
  return ndb.Key('addFriend', user_id)

def ChatGroupMemberKey(group_id=DEFAULT_GROUP_ID):
  """Sub model for representing an author."""
  return ndb.Key('addGroup', group_id)




class HandleConnect(webapp2.RequestHandler):
  """ Send a welcome message and notifies all other users. """
  def post(self):
    user_id = self.request.get('from')
    chat_user = ChatUser.get_by_id(user_id)

    existing_users = ChatUser.query(ChatUser.key != chat_user.key)

    channel.send_message(chat_user.key.string_id(),
                         'Welcome, %s! ' %
                         (chat_user.nickname, ))
    for existing_user in existing_users:
      channel.send_message(existing_user.key.string_id(),
                           '%s joined' % chat_user.nickname)


class HandleDisconnect(webapp2.RequestHandler):
  """ Deletes the user model and notifies all other users. """
  def post(self):
    user_id = self.request.get('from')
    chat_user = ChatUser.get_by_id(user_id)
    # chat_user.key.delete()

    # for user in ChatUser.query():
    #   channel.send_message(user.key.string_id(), '%s left' % chat_user.nickname)


class HandleSend(webapp2.RequestHandler):
  """ When a user sends a message to be echoed to all other users. """
  def post(self):
    user_id = users.get_current_user().user_id()
    chat_user = ChatUser.get_by_id(user_id)
    curr_user_email = users.get_current_user().email()

    data = self.request.get('data')
    for recipient in ChatUser.query():
      cur_group_query = Friend.query(ancestor= ChatGroupMemberKey(user_id))
      for member in cur_group_query:
        if (recipient.nickname == users.get_current_user().nickname()):
          channel.send_message(recipient.key.string_id(),
                           '%s: %s' % (chat_user.nickname, cgi.escape(data)))
          break
        if (recipient.nickname == member.nickname):
          
          channel.send_message(recipient.key.string_id(),
                           '%s: %s' % (chat_user.nickname, cgi.escape(data)))
          break


class HandleMain(webapp2.RequestHandler):
  """ Renders index.html an initializes the chat room channel. """
  @login_required
  def get(self):
    user = users.get_current_user()
    chat_user = ChatUser.get_or_insert(user.user_id(),
                                       nickname = user.nickname())

    token = channel.create_channel(chat_user.key.string_id())
    template = jinja_environment.get_template('index.html')
    self.response.out.write(template.render({ 'token': token, 'user_id':chat_user.nickname }))


############################


class SearchforUsers(webapp2.RequestHandler):
  """ When a user sends a message to be echoed to all other users. """
  def get(self):
    user = users.get_current_user()
    user_id = users.get_current_user().user_id()
    chat_user = ChatUser.get_or_insert(user.user_id(),
                                       nickname = user.nickname())

    search_result = self.request.get('search')
    search_result_lower = search_result.lower()

    users_list = ChatUser.query()
    friend_list = Friend.query(ancestor = friend_list_key(user_id.lower()))
    group_list = ChatGroup.query()
    token = channel.create_channel(chat_user.key.string_id())

    template = jinja_environment.get_template('search.html')
    self.response.out.write(template.render({ 'users': users_list , 'user_id': user_id, 'friend_list': friend_list, 'group_list': group_list, 'token': token,'search_result': search_result_lower }))



class HandleFriendList(webapp2.RequestHandler):
  """ When a user sends a message to be echoed to all other users. """
  def get(self):
    user = users.get_current_user()
    user_id = users.get_current_user().user_id()
    chat_user = ChatUser.get_or_insert(user.user_id(),
                                       nickname = user.nickname())

    data = self.request.get('data')
    users_list = ChatUser.query()

    friend_list = Friend.query(ancestor = friend_list_key(user_id.lower()))

    group_list = ChatGroup.query()

    token = channel.create_channel(chat_user.key.string_id())


    template = jinja_environment.get_template('add_friends.html')
    self.response.out.write(template.render({ 'users': users_list , 'user_id': user_id, 'friend_list': friend_list, 'group_list': group_list, 'token': token}))

class addFriendExecute (webapp2.RequestHandler):

  def post(self):
      user_id = self.request.get('user_id',DEFAULT_USER_ID)




      friends = self.request.get('check_list', allow_multiple=True)
      for friend in friends:
        existance = False
        friend_list = Friend.query(ancestor=friend_list_key(user_id.lower()))
        for cur_friend in friend_list:
          if (cur_friend.nickname == friend):
            existance = True
            break
        if (existance == False):
          single_friend = Friend(parent=friend_list_key(user_id.lower()))
          single_friend.nickname = friend
          single_friend.put()

      self.redirect('/add_friends')

class addGroup (webapp2.RequestHandler):

  def post(self):
      user_id = self.request.get('user_id',DEFAULT_USER_ID)

      members = self.request.get('check_list', allow_multiple=True)
      group_name = self.request.get('group_name')
      random.seed(datetime.now())
      r = random.randint(0,1000000)
      group_id = str(r)

      single_group = ChatGroup()
      single_group.group_id = group_id
      single_group.group_name = group_name
      single_group.put()

      for member in members:
        single_member = Friend(parent=ChatGroupMemberKey(group_id))
        single_member.nickname = member
        single_member.put()

      self.redirect('/add_friends')


class removeFriends (webapp2.RequestHandler):

  def get(self):
    user_id = users.get_current_user().user_id()
    chat_user = ChatUser.get_by_id(user_id)

    users_list = ChatUser.query()

    friend_list = Friend.query(ancestor=friend_list_key(user_id.lower()))
    group_list = ChatGroup.query()

    template = jinja_environment.get_template('delete_friends.html')
    self.response.out.write(template.render({ 'users': users_list , 'user_id': user_id, 'friend_list': friend_list, 'group_list': group_list}))

class deleteFriendExecute (webapp2.RequestHandler):

  def post(self):
      user_id = users.get_current_user().user_id()

      friends = self.request.get('check_list', allow_multiple=True)

      for target in friends:
        friend_list = Friend.query(ancestor= friend_list_key(user_id.lower()))
        for friend in friend_list:
          if (friend.nickname == target):
            friend.key.delete()

      self.redirect('/delete_friends')


class deleteGroup (webapp2.RequestHandler):

  def post(self):
      user_id = users.get_current_user().user_id()
      groups_to_delete = self.request.get('check_list', allow_multiple=True)

      

      for group_to_delete in groups_to_delete:
        group_list = ChatGroup.query()
        for group in group_list:
          if (group.group_id == group_to_delete):
            group.key.delete()
            break

      self.redirect('/delete_friends')


class chooseGroup (webapp2.RequestHandler):

  def post(self):
    user_id = users.get_current_user().user_id()
    group_id = self.request.get('check_list')

    cur_group_query = Friend.query(ancestor= ChatGroupMemberKey(user_id))
    for member in cur_group_query:
      member.key.delete()

    if (group_id != 'all'):
      next_group_query = Friend.query(ancestor = ChatGroupMemberKey(group_id))
      for member in next_group_query:

        new_friend = Friend(parent = ChatGroupMemberKey(user_id))
        new_friend.nickname = member.nickname
        new_friend.put()
      

    if (group_id == 'all'):
      next_group_query = ChatUser.query()
      for member in next_group_query:

        new_friend = Friend(parent = ChatGroupMemberKey(user_id))
        new_friend.nickname = member.nickname
        new_friend.put()

    self.redirect('/?')


jinja_environment = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

app = webapp2.WSGIApplication([
  ('/', HandleMain),
  ('/send', HandleSend),
  ('/_ah/channel/connected/', HandleConnect),
  ('/_ah/channel/disconnected/', HandleDisconnect),

  ('/add_friends', HandleFriendList),
  ('/addFriendExexute', addFriendExecute),
  ('/delete_friends', removeFriends),
  ('/deleteFriendExecute', deleteFriendExecute),
  ('/addGroup', addGroup),
  ('/chooseGroup', chooseGroup),
  ('/deleteGroup', deleteGroup),
  ('/search', SearchforUsers)
], debug=True)
