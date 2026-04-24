from psychopy import visual

class PhotoDiodeMarker:
    def __init__(self, win, size=(60, 60), pos=None):
        self.win = win
        # 위치 자동 계산 (좌하단)
        if pos is None:
            w, h = win.size
            self.pos = (-w // 2 + size[0] // 2, -h // 2 + size[1] // 2)
        else:
            self.pos = pos
            
        self.rect = visual.Rect(
            win, width=size[0], height=size[1],
            fillColor=[1, 1, 1], lineColor=[1, 1, 1], # 순백색
            pos=self.pos, units='pix'
        )
        
        self.duration = 3          
        self.current_frame = 0     
        self.event_frame = -100    

    def trigger(self):
        # current_frame에 event_frame 담기
        self.event_frame = self.current_frame

    def update(self):
        # win.filp() 전에 갱신
        self.current_frame += 1

    def draw(self):
       # duration 동안 frame 표시
        diff = self.current_frame - self.event_frame
        if 0 <= diff < self.duration:
            self.rect.draw()