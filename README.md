# Applicator Kit for Modo

**Applicator Kit for Modo** allow you to apply Apple ARKit Face Tracking data from your iPhone or iPad with a TrueDepth camera to your characters in Modo. Apple ARKit Face Tracking enables your iPhone or iPad to track a performer’s head location as well as [over 50 unique Blend Shape coefficients](https://developer.apple.com/documentation/arkit/arfaceanchor/blendshapelocation) (Morph Targets in Modo), all at 60 frames per second. With **Applicator Kit for Modo**, you can take this data and apply it to your characters in Modo in 4 Easy Steps:

1. Define your mapping file
2. Record your face capture performance
3. Transfer the data to your computer
4. Apply the data to your character

### **Overview Videos:**
- [Overview](https://www.youtube.com/watch?v=jOUwkQ5hkuI)
- [Walkthrough](https://www.youtube.com/watch?v=nm-js_KEan4)
- [Mapping Files](https://www.youtube.com/watch?v=1tP6rzJ5bVk)

### **Installation:**
1. Open Modo
2. System > Open User Folder
3. Copy the Applicator folder into the Kits folder
4. Restart Modo

### **Key Features:**
- **Item Hierarchy Target:** apply the data to all mapped targets within a hierarchy of items in a scene
- **Actor and Action Target:** apply the data to an Actor, and optionally as an Action (new or existing)
- **Mapping File:** allows you to configure the target Morph Maps and Items to apply tracking data to
- **Multi-Target:** allows you to apply a single Blend Shape tracking data to multiple Morph Maps
- **Independent Enable/Disable:** gives you full control over which data points to apply to your scene
- **Multiplier:** sometimes the capture is just too subtle (or too extreme) and not giving you the performance, you need. The multiplier allows you increase (or decrease) the value of the tracking data to your scene
- **Value Shift:** like the multiplier, the value shift allows you to tweak the performance, but rather than multiplying the tracking data, it shifts the value up or down using a constant value (super handy for adjusting head rotation data)
- **Smoothing Algorithm:** optionally apply a smoothing algorithm to the tracking data
- **FPS Conversion:** automatically converts the 60fps recording data to scene’s fps. Support fps options: 60, 50, 48, 30, 29.97, 25 and 24.
- **Neutral Algorithm:** by optionally providing a neutral facial capture (~5 seconds recording of the performer’s face in a neutral state), the algorithm adjusts the capture data to cater for the unique facial shape of the performer.
- **Start Frame:** specify which frame to start the data application to
- **Skip Capture Frames:** specify how many frames from the recording you’d like to skip

### **Supported Face Tracking Apps:**
Note:
Applicator Kit does not capture face tracking data, it only applies the data to your scenes in Modo. Please use [Live Link Face](https://apps.apple.com/us/app/live-link-face/id1495370836) (free courtesy of Unreal Engine) to capture the facial performance.
