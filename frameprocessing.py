import cv2  
import numpy as np  
import math  
from ui import frame_labels  


def calculate_viscosity(R, P):
    # Calculate viscosity using v = π * R^4 * P 
    return math.pi * R**4 * P

# process video and store values
def process_video(cap, nozzle_diameter, frame_count, microns_per_pixel):
    diameters = []  
    selected_frames = {}  # Dictionary to store key frames by label
    max_diameter = 0  # Variable to track the maximum detected diameter
    max_frame_idx = 0  # Index of the frame with the maximum diameter
    firstFrame = None  # Store the first processed frame for reference
    frame_indices = {}  # Dictionary to store frame indices corresponding to selected key frames

    # Loop over all frames in the video capture
    for i in range(frame_count):
        ret, frame = cap.read()  # Read the next frame
        if not ret:  # If frame not read successfully, break loop
            break
#image proccessing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) #grayscale
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))  #contrast enhancement
        gray_eq = clahe.apply(gray)  # Apply CLAHE to grayscale image
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))  # Create elliptical structuring element for morphology ops
        tophat = cv2.morphologyEx(gray_eq, cv2.MORPH_TOPHAT, kernel)  # Apply top-hat morphological operation to highlight bright regions
        glare_removed = cv2.subtract(gray_eq, tophat)  # Remove glare by subtracting top-hat result from equalized image
        blurred = cv2.GaussianBlur(glare_removed, (5, 5), 0)  # Blur the image to reduce noise
        edges = cv2.Canny(blurred, 50, 150)  # Detect edges using Canny edge detector
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)  # Close gaps in edges using morphological closing
        cleaned = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel, iterations=1)

        if firstFrame is None:  # For the very first frame processed
            firstFrame = closed  # Store it for reference
            continue  # Skip rest of loop to avoid processing on first frame

        thresh = cv2.threshold(closed, 20, 255, cv2.THRESH_BINARY)[1]  # Threshold the closed edges image to binary
        roi_top = int(thresh.shape[0] * 0.25)  # Define region of interest starting 25% from top vertically
        roi_thresh = thresh[roi_top:, :]  # Crop thresholded image to ROI (bottom 75%)
        contours, _ = cv2.findContours(roi_thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # Find contours in ROI
        diameter = 0  # Initialize diameter for this frame to zero

        if contours:  # If any contours are found
            MIN_AREA = 100  # Minimum contour area to be considered valid
            MAX_AREA = 10000  # Maximum contour area to be considered valid
            # Filter contours by area constraints
            valid = [c for c in contours if MIN_AREA < cv2.contourArea(c) < MAX_AREA]
            valid_filtered = []  # Further filtered contours based on aspect ratio

            for c in valid:  # For each valid contour
                x, y, w, h = cv2.boundingRect(c)  # Get bounding rectangle dimensions
                if h / float(w) < 3:  # Check if height-to-width ratio is less than 3 (filter out tall thin contours)
                    valid_filtered.append(c)  # Add contour to filtered list

            if valid_filtered:  # If filtered contours exist
                largest = max(valid_filtered, key=cv2.contourArea)  # Find contour with largest area
                epsilon = 0.01 * cv2.arcLength(largest, True)  # Calculate approximation accuracy for contour polygon
                largest = cv2.approxPolyDP(largest, epsilon, True)  # Approximate contour shape
                (x, y), radius = cv2.minEnclosingCircle(largest)  # Get minimum enclosing circle of the largest contour
                y += roi_top  # Adjust y coordinate because ROI was cropped
                diameter = 2 * radius * microns_per_pixel  # Calculate diameter in microns from radius and scale factor

                if diameter > max_diameter:  # If this diameter is the largest so far
                    max_diameter = diameter  # Update max diameter
                    max_frame_idx = i  # Update index of frame with max diameter

                # Draw the contour on the frame in green with thickness 2
                cv2.drawContours(frame, [largest + [0, roi_top]], -1, (0, 255, 0), 2)

        diameters.append(diameter)  # Append diameter for current frame to list

        # Save frames for specific labels at certain frame indices or conditions
        if i == 0:
            selected_frames["Pre Droplet"] = frame.copy()  # Frame before any droplet appears
            frame_indices["Pre Droplet"] = i
        elif i == 1:
            selected_frames["Before Extrusion"] = frame.copy()  # Frame right before extrusion starts
            frame_indices["Before Extrusion"] = i
        elif diameter > 5 and "Beginning Extrusion" not in selected_frames:
            selected_frames["Beginning Extrusion"] = frame.copy()  # First frame where diameter crosses threshold 5 microns
            frame_indices["Beginning Extrusion"] = i
        elif i == max_frame_idx:
            selected_frames["Max Diameter"] = frame.copy()  # Frame with maximum detected diameter
            frame_indices["Max Diameter"] = i
        elif i > max_frame_idx and "Post Extrusion" not in selected_frames:
            selected_frames["Post Extrusion"] = frame.copy()  # First frame after max diameter frame
            frame_indices["Post Extrusion"] = i

        firstFrame = closed  # Update firstFrame to current closed image for next iteration

    cap.release()  # Release video capture object to free resources

    # --- Manual Measurement via Mouse Callback ---
    if "Max Diameter" in selected_frames:
        # Define a mouse callback function to capture two points clicked by user
        def click_event(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:  # If left mouse button clicked
                param.append((x, y))  # Append clicked point coordinates to param list
                cv2.circle(temp_frame, (x, y), 5, (0, 0, 255), -1)  # Draw a small red circle at click location
                cv2.imshow("Select Two Points", temp_frame)  # Update window to show circle

        temp_frame = selected_frames["Max Diameter"].copy()  # Copy frame for annotation
        points = []  # List to store clicked points
        cv2.imshow("Select Two Points", temp_frame)  # Show frame to user for clicking
        cv2.setMouseCallback("Select Two Points", click_event, points)  # Set mouse callback to capture clicks

        while len(points) < 2:  # Wait until user clicks two points
            cv2.waitKey(1)
        cv2.destroyWindow("Select Two Points")  # Close the window after two points selected

        # Calculate distance between two clicked points
        dx = points[0][0] - points[1][0]  # Difference in x coordinates
        dy = points[0][1] - points[1][1]  # Difference in y coordinates
        pixel_distance = (dx**2 + dy**2)**0.5  # Euclidean distance in pixels
        manual_diameter = pixel_distance * microns_per_pixel  # Convert pixels to microns

        # Warn user if manual diameter is suspiciously close to nozzle diameter
        if manual_diameter < 1.2 * nozzle_diameter:
            print("Warning: Selected droplet diameter is suspiciously close to nozzle diameter.")

        diameters[max_frame_idx] = manual_diameter  # Replace max diameter with manual measurement
        max_diameter = manual_diameter  # Update max diameter to manual measurement

        pt1 = (int(points[0][0]), int(points[0][1]))  # First point tuple
        pt2 = (int(points[1][0]), int(points[1][1]))  # Second point tuple
        cv2.line(selected_frames["Max Diameter"], pt1, pt2, (255, 0, 0), 2)  # Draw blue line between points on frame

    # Return the key frames, their indices, list of diameters over frames, max diameter and frame index of max diameter
    return selected_frames, frame_indices, diameters, max_diameter, max_frame_idx
