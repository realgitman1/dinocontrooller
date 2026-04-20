Dino controller made with Gemini
<img width="160" height="120" alt="image" src="https://github.com/user-attachments/assets/3cc344a7-8090-4332-9a70-d1cb7851f70e" />

---
1. First of all, put the dino game on the newest browser window (it's fine if it's not necessarily a google dino game)

2. If you run dinocontroller.exe in the dist folder, you will see a terminal window, and you can turn on the webcam and play it using motion capture.
---
It's an application that lets you control Dino games through motion capture. Most importantly, your 'most recent browser window should be the one running Dino games'. (It doesn't have to be Google site, it's just the latest browser window that gives commands.)

### Be careful. It should be the most up-to-date browser window

# 🦖 T-Rex Game Controller Logic (Hand Gestures)

The following table explains the control mapping based on the number of fingers detected by the webcam.

| Finger Count | Game Action | Description |
| :--- | :--- | :--- |
| **3 or more** | **JUMP** | Executes the **`Space`** key to jump over obstacles. |
| **2** | **NEUTRAL** | Returns to normal running; releases the **`Down`** key if it was held. |
| **1 or fewer (Excl. 0)** | **DUCK** | Holds the **`Down`** key to crouch and avoid low-flying birds. |
| **0 (Not detected)** | **RESET / NEUTRAL** | Stops all actions when the hand is missing or too small (noise reduction). |

---

### Control Summary
-  **3+ Fingers**: Jump
- **2 Fingers**: Neutral / Run
- **1 Finger**: Duck
- **0 Fingers**: Reset Action

---
### If you give me a tip for the game, it's easier to control it by holding your hand as if you're holding something and then making a motion that only opens when you jump
---
#### Dino synth is made with prompt engineering for fun, and you can think of it as synth using motion capture. Try to use it in a fun way because the pitch of the sound is recognized as the volume of the sound up and down the object
