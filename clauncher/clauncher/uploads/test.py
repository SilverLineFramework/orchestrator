import time
import sys
import threading
import os

fruits = ["Apple", "Banana", "Cherry", "Blackberries", "Clementine", "Figs", "Mango", "Nectarine", "Pineapple", "Strawberries", "Watermelon", "Tangerine"]

def _read_stdin(callback):
  for line in sys.stdin:
      if 'Exit' == line.rstrip():
          break
      if len(line) > 1:
        callback(line.rstrip())

def onMessage(msg):
      print(f'Received: {msg}')

def main():
  t = threading.Thread(name='stdin_thread', target=_read_stdin, args=(onMessage,))
  t.start()
  
  while t.isAlive():
    for f in fruits:
      print(f)
      time.sleep(1)
      if not t.isAlive():
        break
        
if __name__ == "__main__":
    main()

