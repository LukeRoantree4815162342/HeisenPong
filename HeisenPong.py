from kivy.config import Config
Config.set('graphics', 'width', '1200')
Config.set('graphics', 'height', '700')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.properties import (
NumericProperty, ReferenceListProperty, ObjectProperty, StringProperty
)
from kivy.uix.slider import Slider
from kivy.vector import Vector
from kivy.clock import Clock
#from kivy.core.audio import SoundLoader
from random import random
from time import sleep

class PongPaddle(Widget):
    score = NumericProperty(0)

    def bounce_ball(self, ball):
        if self.collide_widget(ball):
            vx, vy = ball.velocity
            offset = (ball.center_y - self.center_y) / (self.height / 2)
            bounced = Vector(-1 * vx, vy)
            vel = bounced * 1.1
            ball.velocity = vel.x, vel.y + offset


class CommutationRelator():
    def __init__(self, hbar=15, pos_uncert=50):
        
        assert pos_uncert > 0, "Uncertainty in position must be positive"
        assert hbar > 0, "Commutation relation must be positive"

        # Commutation relation:
        # pos_uncert * mom_uncert = hbar 
        # (note: fixed mass, so sub mom for vel)
        self.hbar = hbar
        self.pos_uncert = pos_uncert*3
        self.vel_uncert = hbar/self.pos_uncert

class PongBall(Widget):
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)
    pos_uncert = 50
    pos_perturbation = (0,0)

    def move(self, vball):
        self.cr = CommutationRelator(10, self.pos_uncert)
        if random()<0.5:
            self.pos_perturbation = (self.cr.pos_uncert*(random()-0.5), self.cr.pos_uncert*(random()-0.5))

        #if random()<0.1:
        #    self.velocity_x += perturbation[0]
        #    self.velocity_y += perturbation[1]
        self.pos = Vector(*vball.velocity) + vball.pos + Vector(*self.pos_perturbation)

class PongVirtualBall(Widget):
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    pos_uncert = 50
    velocity = ReferenceListProperty(velocity_x, velocity_y)
    vel_perturbation = (0,0)

    def move(self):
        #factor = 2
        #perturbation = (factor*(random()-0.5), factor*(random()-0.5))
        #if random()<0.1:
        #    self.velocity_x += perturbation[0]
        #    self.velocity_y += perturbation[1]
        self.cr = CommutationRelator(10, self.pos_uncert)
        if random()<0.15:
            self.vel_perturbation = (self.cr.vel_uncert*(random()-0.5), self.cr.vel_uncert*(random()-0.5))
        self.velocity = self.velocity[0]+ self.vel_perturbation[0] , self.velocity[1] + self.vel_perturbation[1]
        self.pos = Vector(*self.velocity) + self.pos #+ 3*Vector(*perturbation)

class PongEndmsg(Widget):
    win_msg = StringProperty("")
    def write(self, winner):
        self.win_msg = "Player {} Wins!".format(winner)

class PongScoremsg(Widget):
    score_msg = StringProperty("")
    def announce_point(self):
        self.score_msg = "Point!"
    def clear_announcement(self):
        self.score_msg = ""


class PongGame(Widget):
    game_in_play = True
    frame_count = 0
    last_point_frame = 0
    ball = ObjectProperty(None)
    vball = ObjectProperty(None)
    player1 = ObjectProperty(None)
    player2 = ObjectProperty(None)
    my_slider = ObjectProperty(None)
    max_score = 0
    endmsg = ObjectProperty(None)
    score_msg = ObjectProperty(None)
    win_score = 10
    

    def __init__(self, **kwargs):
        super(PongGame, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(None, self)
        if not self._keyboard:
            return
        self._keyboard.bind(on_key_down=self.on_keyboard_down)
        self.my_slider.bind(value=self.OnSliderValueChange)

    def on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'm':
            self.player2.y -= 100
        elif keycode[1] == 'k':
            self.player2.y += 100
        elif keycode[1] == 'z':
            self.player1.y -= 100
        elif keycode[1] == 'a':
            self.player1.y += 100
        else:
            return False
        return True

    def serve_ball(self, vel=(5, 0)):
        self.ball.center = self.center
        self.ball.velocity = vel
        self.vball.center = self.center
        self.vball.velocity = vel

    def update(self, dt):
        if self.game_in_play:
            self.frame_count += 1
            self.ball.move(self.vball)
            self.vball.move()


        # bounce ball off bottom or top
        if (self.ball.y < self.y) or (self.ball.top > self.top):
            self.ball.velocity_y *= -1

        if (self.vball.y < self.y) or (self.vball.top > self.top):
            self.vball.velocity_y *= -1


        # went off to a side to score point?
        # changed to depend on vball rather than ball
        factor = 1.15**self.max_score
        if (self.ball.x < self.x) or (self.ball.x > self.width):
            if self.ball.x < self.x:
                self.player2.score += 1
                self.score_msg.announce_point()
                self.last_point_frame = self.frame_count
                self.serve_ball(vel=(4*factor, factor*3*(random()-0.5)))
            elif self.ball.x > self.width:
                self.player1.score += 1
                self.score_msg.announce_point()
                self.last_point_frame = self.frame_count
                self.serve_ball(vel=(-4*factor, factor*3*(random()-0.5)))

            self.max_score = max([self.player1.score, self.player2.score])

            if self.max_score >= self.win_score:
                self.endmsg.write(1 if self.player1.score > self.player2.score else 2)
                self.ball.velocity = (0,0)
                self.vball.velocity = (0,0)
                self.game_in_play = False
                self.score_msg.clear_announcement()

        else:
            if (self.frame_count - self.last_point_frame) > 15:
                self.score_msg.clear_announcement()
            # bounce of paddles
            self.player1.bounce_ball(self.ball)
            self.player2.bounce_ball(self.ball)
            self.player1.bounce_ball(self.vball)
            self.player2.bounce_ball(self.vball)
            

    def on_touch_move(self, touch):
        if touch.x < self.width / 3:
            self.player1.center_y = touch.y
        if touch.x > self.width - self.width / 3:
            self.player2.center_y = touch.y
            
    def OnSliderValueChange(self, instance, value):
        self.ball.pos_uncert = value
        self.vball.pos_uncert = value

class PongApp(App):
    def build(self):
        #sound = SoundLoader.load('mytest.wav')
        #sound.loop = True
        game = PongGame()
        game.serve_ball(vel=((2*(random()>0.5)-1)*4, 3*(random()-0.5)))
        sleep(10)
        Clock.schedule_interval(game.update, 1.0 / 60.0)
        return game


if __name__ == '__main__':
    PongApp().run()
