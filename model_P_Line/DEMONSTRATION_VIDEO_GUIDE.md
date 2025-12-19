# 🎥 Demonstration Video Feature - Complete Guide

## ✅ What's New?

Your data collection script now shows **demonstration videos** alongside the camera feed! This makes it much easier for people who don't know the signs to learn and record them correctly.

---

## 🎯 How It Works

### **Side-by-Side Display**

```
┌─────────────────────────────────────────────────────┐
│  DEMONSTRATION  │         YOUR CAMERA               │
│                 │                                   │
│   [Demo Video]  │   [Your Webcam with Landmarks]   │
│   Playing on    │   Live feed showing your          │
│   loop          │   hand movements                  │
│                 │                                   │
└─────────────────────────────────────────────────────┘
```

- **Left side:** Demonstration video showing how to do the sign (loops continuously)
- **Right side:** Your webcam feed with MediaPipe landmarks
- **No sound:** Videos play silently so you can focus on the movements
- **Auto-loop:** Demo video repeats until you finish recording that sign

---

## 📁 Folder Structure

```
model_P_Line/
├── Demonstration_videos/
│   ├── Week_1_Greetings/
│   │   ├── hello.mp4          ✅ Currently available
│   │   ├── goodbye.mp4        ⚠️  Add later
│   │   ├── yes.mp4            ⚠️  Add later
│   │   ├── no.mp4             ⚠️  Add later
│   │   ├── welcome.mp4        ⚠️  Add later
│   │   ├── awake.mp4          ⚠️  Add later
│   │   ├── alive.mp4          ⚠️  Add later
│   │   └── start.mp4          ⚠️  Add later
│   ├── Week_2_Manners/
│   │   ├── please.mp4
│   │   ├── thank_you.mp4
│   │   └── ... (add later)
│   └── ... (other weeks)
├── config.py                   ✅ Updated with demo video path
└── data_collection.py          ✅ Updated to show demo videos
```

---

## 🔧 What Was Changed

### 1. **config.py** - Added Demo Video Support

```python
# New path for demonstration videos
DEMO_VIDEOS_PATH = os.path.join('Demonstration_videos')

# New helper function
def get_demo_video_path(action):
    """
    Returns the path to the demonstration video for a specific sign.
    Returns None if the video doesn't exist.
    """
    video_filename = f"{action}.mp4"
    video_path = os.path.join(DEMO_VIDEOS_PATH, ACTIVE_WEEK, video_filename)
    
    if os.path.exists(video_path):
        return video_path
    else:
        return None
```

### 2. **data_collection.py** - Updated to Show Demo Videos

**New Features:**
- ✅ Loads demonstration video for each sign
- ✅ Shows demo video on the left, camera on the right
- ✅ Loops demo video continuously
- ✅ Resizes demo video to match camera height
- ✅ Adds labels: "DEMONSTRATION" and "YOUR CAMERA"
- ✅ Gracefully handles missing demo videos (shows camera only)
- ✅ Releases demo video when moving to next sign

**New Functions:**
```python
def get_demo_frame(demo_cap, target_height):
    """Get next frame from demo video, loop when it ends"""
    
def combine_frames(camera_frame, demo_frame):
    """Combine camera and demo frames side by side"""
```

---

## 🚀 How to Use

### **Step 1: Run Data Collection**

```bash
cd model_P_Line
python data_collection.py
```

### **Step 2: What You'll See**

#### **Initial Screen (Before Recording)**
```
┌─────────────────────────────────────────────────────┐
│  DEMONSTRATION  │         YOUR CAMERA               │
│                 │                                   │
│   [hello demo]  │   SIGN: HELLO                    │
│   playing...    │   You will record 30 videos      │
│                 │   Press SPACE to start recording │
│                 │   Press Q to quit                │
└─────────────────────────────────────────────────────┘
```

#### **During Recording**
```
┌─────────────────────────────────────────────────────┐
│  DEMONSTRATION  │         YOUR CAMERA               │
│                 │                                   │
│   [hello demo]  │   RECORDING: HELLO               │
│   playing...    │   Video 5/30 | Frame 15/30       │
│                 │   [Your hands with landmarks]    │
└─────────────────────────────────────────────────────┘
```

#### **Review Screen (After 30 Videos)**
```
┌─────────────────────────────────────────────────────┐
│  DEMONSTRATION  │         YOUR CAMERA               │
│                 │                                   │
│   [hello demo]  │   COMPLETED: HELLO               │
│   playing...    │   Recorded 30 videos             │
│                 │   Are you happy with these?      │
│                 │   Press BACKSPACE to retake      │
│                 │   Press any key to continue      │
└─────────────────────────────────────────────────────┘
```

---

## 📝 Current Status

### **Available Demo Videos:**
- ✅ `hello.mp4` - Week_1_Greetings

### **What Happens If Demo Video Is Missing:**
- ⚠️  Script shows a warning: `"No demonstration video found for 'goodbye'"`
- ✅ Script continues normally, showing only the camera feed
- ✅ You can still record data without the demo video

---

## 🎬 Adding More Demo Videos

### **Video Requirements:**
- **Format:** `.mp4` (recommended)
- **Naming:** Must match the sign name exactly (e.g., `goodbye.mp4`, `yes.mp4`)
- **Location:** `Demonstration_videos/Week_1_Greetings/`
- **Sound:** Not required (script plays videos silently)
- **Length:** Any length (video will loop automatically)
- **Quality:** Any resolution (script auto-resizes to match camera height)

### **Steps to Add:**

1. **Record or obtain demo video** for a sign (e.g., "goodbye")
2. **Save as:** `goodbye.mp4`
3. **Place in:** `model_P_Line/Demonstration_videos/Week_1_Greetings/`
4. **Run data collection** - it will automatically detect and use the video!

### **Example:**
```bash
# Add demo video for "goodbye"
model_P_Line/Demonstration_videos/Week_1_Greetings/goodbye.mp4

# Run data collection
python data_collection.py

# Output:
# ✅ Loaded demonstration video: Demonstration_videos\Week_1_Greetings\goodbye.mp4
```

---

## 🧪 Testing

### **Test with "hello" (Available Now):**
```bash
cd model_P_Line
python data_collection.py
```

**Expected Output:**
```
--- CONFIGURATION LOADED ---
Active Schedule: Week_1_Greetings
Target Words (8): ['hello' 'goodbye' 'yes' 'no' 'welcome' 'awake' 'alive' 'start']

--- PREPARING FOR ACTION: hello ---
✅ Loaded demonstration video: Demonstration_videos\Week_1_Greetings\hello.mp4
```

**You should see:**
- Demo video on the left showing "hello" sign
- Your camera feed on the right
- Both playing simultaneously

---

## ⚙️ Configuration

### **Active Week:**
The script automatically looks for demo videos in the folder matching `ACTIVE_WEEK`:

```python
# In config.py
ACTIVE_WEEK = 'Week_1_Greetings'  # Looks in Demonstration_videos/Week_1_Greetings/
```

### **Change Week:**
```python
ACTIVE_WEEK = 'Week_2_Manners'  # Looks in Demonstration_videos/Week_2_Manners/
```

---

## 🎉 Benefits

1. ✅ **Easier Learning** - People can see exactly how to do each sign
2. ✅ **Better Quality** - More accurate recordings when following a demo
3. ✅ **Faster Collection** - No need to look up signs elsewhere
4. ✅ **Consistent Data** - Everyone follows the same demonstration
5. ✅ **Graceful Fallback** - Works even if demo video is missing

---

## 🔄 Workflow

```
1. User starts data_collection.py
2. Script loads demo video for "hello"
3. Shows demo + camera side by side
4. User presses SPACE to start
5. Records 30 videos while watching demo
6. Review screen (keep or retake)
7. Move to next sign ("goodbye")
8. Script loads new demo video for "goodbye"
9. Repeat...
```

---

## ✅ Summary

**What's Working:**
- ✅ Demo video support fully integrated
- ✅ Side-by-side display (demo + camera)
- ✅ Auto-loop for continuous playback
- ✅ Graceful handling of missing videos
- ✅ Config file aligned with new feature
- ✅ "hello" demo video ready to use

**Next Steps:**
1. Test with "hello" demo video
2. Add more demo videos as you create them
3. Collect high-quality data with visual guidance!

---

**Ready to collect data with demonstration videos! 🚀**

