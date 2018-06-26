import unittest
from app import app, User, Message, db


class MyAppUnitTestCase(unittest.TestCase):
    def test_show_user_index(self):
        client = app.test_client()
        result = client.get("/users")
        self.assertEqual(result.status_code, 200)

    def test_create_user(self):
        client = app.test_client()
        result = client.post(
            '/users',
            data={
                'first_name': 'dummy',
                "last_name": "stupid"
            },
            follow_redirects=True)
        self.assertIn(b'dummy', result.data)

    def test_update_user(self):
        client = app.test_client()
        result = client.patch(
            '/users/1',
            data={
                'profile_picture': 'http://ru-an.info/Photo/QNews/n28499/1.jpg'
            })
        self.assertIn(b'http://ru-an.info/Photo/QNews/n28499/1.jpg',
                      result.data)

        user = User.query.get(1)
        self.assertEqual(user.picture_url,
                         'http://ru-an.info/Photo/QNews/n28499/1.jpg')

    def test_delete_message(self):
        client = app.test_client()
        new_message = Message(
            author='Kelley', content='delete bitch', user_id='2')
        db.session.add(new_message)
        db.session.commit()

        new_id = new_message.id
        result = client.delete('/users/' + str(new_message.user_id) +
                               'messages/' + str(new_message.id))
        self.assertNotIn(b'<p> delete bitch </p>', result.data)


if __name__ == "__main__":
    unittest.main(verbosity=9)
