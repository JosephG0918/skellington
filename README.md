This project provides real-time object tracking for my animatronic head. Tracking is time-based, meaning
control alternates between the eyes and the neck instead of driving both constantly. Exponential Moving Average (EMA)
smoothing is used extensively throughout follower.py to prevent sudden movements and produce smoother, more natural motion.
EMA is also applied to secondary behaviors such as the jaw and eyelids, helping the animatronic feel more alive.

I had to switch to Picamera2 because I was having trouble getting the original script to work on the newer Raspberry Pi OS (Trixie). 
Picamera2 turned out to be a lifesaver and worked splendidly alongside OpenCV without any issues.
