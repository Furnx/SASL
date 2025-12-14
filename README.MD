Here is the updated `README.md` file. I have added the **Verification Step**, the **Training & Prediction** instructions, and polished the workflow to match the new robust scripts.

Copy and paste this directly into your repository.

-----

# 🇿🇦 The Cohort 2025 Legacy Project: SASL AI Model

**Welcome to the team.** We are building South Africa's first large-scale, open-source Sign Language AI dataset. This is our legacy.

-----

## 🚀 Quick Start (Do this first\!)

If you are joining the team for the first time, follow these steps to set up your laptop.

### 1\. Clone the Repo

```bash
git clone https://github.com/[YOUR_USERNAME]/sasl-legacy-project.git
cd sasl-legacy-project
```

### 2\. Create a Virtual Environment (Recommended)

This keeps your laptop clean.

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3\. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4\. 🛠️ Run the Diagnostic Tool (Critical)

We have built a tool to check if your camera and libraries are working.

```bash
python verify_setup.py
```

*If you see "🎉 YOU ARE READY TO START\!", proceed. If not, follow the on-screen fixes.*

-----

## 📅 The Weekly Workflow (Data Collection)

We operate on a strict weekly cycle to avoid burnout. **You do not need to edit any code.**

### Step 1: Sync Your Code (Every Monday)

Before you start recording, always make sure you have the latest `config.py` where the weekly signs are set.

Open your terminal in the project folder and run:

```bash
git pull origin main
```

*If you see "Already up to date", you are ready.*

### Step 2: Record Your Data

1.  Make sure you are in a well-lit room with a neutral background.
2.  Run the collection script:
    ```bash
    python data_collection_v2.py
    ```
3.  **Enter your Name:** Use the exact same name every time (e.g., `Thabo`).
4.  **Follow the Screen:** The script will tell you which sign to perform (e.g., "Hello").
      * **Press SPACE** to start recording a sequence.
      * **Perform the sign** naturally.
      * **Repeat** for all 30 sequences.

### Step 3: Upload Your Data (By Friday)

Once you are done, you will see a folder called `MP_Data` in your project directory.

1.  Open the **Shared Google Drive** link: [INSERT\_LINK\_HERE]
2.  Open your local `MP_Data` folder. You will see folders for this week's signs (e.g., `hello`, `yes`).
3.  **Drag and Drop** those sign folders directly into the Google Drive.
      * *Note:* Because the script names your files `YourName_0`, `YourName_1`, you will **NOT** overwrite anyone else's work. Safe to drop\!

-----

## 🧠 Training & Testing (Optional)

Want to see the AI learn? You can train a model on your own computer using the data you just collected.

### To Train the Model

This will build a model using **only** the signs currently active in `config.py`.

```bash
python train.py
```

*This creates `model/sasl_model_v1.h5`.*

### To Test the Model (Real-Time)

This turns on your webcam and predicts the signs you trained.

```bash
python predict.py
```

  * **Note:** If `predict.py` crashes, make sure your `config.py` matches the model you are loading (same number of signs).

-----

## 🚨 Golden Rules for Quality

To make sure our model achieves **95% accuracy**, please follow these rules:

1.  **Lighting:** Light must be **in front of you**, not behind you. If you are a silhouette, the AI cannot see your fingers.
2.  **Background:** A plain wall is best. Avoid messy rooms or people walking behind you.
3.  **Position:** Your upper body (waist to head) should be visible. Your hands must never go "off-screen" while signing.
4.  **Consistency:** Do not rush. Do the sign clearly and naturally.

-----

## 🐛 Troubleshooting

  * **"Camera not opening":** Make sure Zoom/Teams isn't using your camera.
  * **"Module not found":** Run `pip install -r requirements.txt` again.
  * **"Git conflict":** If you accidentally changed the code, run `git reset --hard` then `git pull`.

-----

**Let's build history.** 🚀