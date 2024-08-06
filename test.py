from collections import deque
import threading
import time

class TalkerListener:
    def __init__(self):

        self.buffer = deque()

        listener_thread = threading.Thread(target=self.listener)
        listener_thread.start()

        talker_thread = threading.Thread(target=self.talker)
        talker_thread.start()

        debug_thread = threading.Thread(target=self.debug)
        debug_thread.start()

    
    def listener(self):
        last_msg = None
        while (True):
            if len(self.buffer) <= 0:
                continue

            msg = self.buffer.popleft()
            if last_msg != None and msg != last_msg + 1:
                print("Mismatch found, last message: {}, current message: {}".format(last_msg, msg))
            last_msg = msg
                
                

    def talker(self):
        msg = 0
        while (True):
            self.buffer.append(msg)
            msg += 1
            time.sleep(0.05)

    def debug(self):
        seconds_since_start = 0
        while (True):
            print("Running for {}s".format(seconds_since_start))
            seconds_since_start += 1
            time.sleep(1)

if __name__ == "__main__":
    instance = TalkerListener()
