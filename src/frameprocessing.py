import cv2  
import numpy as np  
import math  
from ui import frame_labels  


def calculate_viscosity(R, P):
    # Calculate viscosity using v = π * R^4 * P 
    return math.pi * R**4 * P

# process video 
def process_video(cap, nozzle_diameter, frame_count, microns_per_pixel):
    diameters = []  
    selected_frames = {}  # store frames
    max_diameter = 0  # track maximum diameter
    max_frame_idx = 0  # select maximum diamter frame
    firstFrame = None  # stored frame
    frame_indices = {}  

    # Loop over all frames in the video capture
    for i in range(frame_count):
        ret, frame = cap.read()  
        if not ret:  
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


# firsy frame store and processing 
        if firstFrame is None:  
            firstFrame = closed 
            continue  

        thresh = cv2.threshold(closed, 20, 255, cv2.THRESH_BINARY)[1]  # Threshold the closed edges image to binary
        roi_top = int(thresh.shape[0] * 0.25)  # Define region of interest starting 25% from top vertically
        roi_thresh = thresh[roi_top:, :]  # Crop thresholded image to ROI (bottom 75%)
        contours, _ = cv2.findContours(roi_thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # Find contours in ROI
        diameter = 0  # Initialize diameter for this frame to zero


# detect contours
        if contours: 
            MIN_AREA = 100  
            MAX_AREA = 10000  
            valid = [c for c in contours if MIN_AREA < cv2.contourArea(c) < MAX_AREA]
            valid_filtered = []  

# track and address each contour
            for c in valid:  
                x, y, w, h = cv2.boundingRect(c)  
                if h / float(w) < 3: 
                    valid_filtered.append(c) 
# more detailed filters for contour
            if valid_filtered: 
                largest = max(valid_filtered, key=cv2.contourArea) 
                epsilon = 0.01 * cv2.arcLength(largest, True) 
                largest = cv2.approxPolyDP(largest, epsilon, True)  
                (x, y), radius = cv2.minEnclosingCircle(largest) 
                y += roi_top  
                diameter = 2 * radius * microns_per_pixel 
# tracking diameter and update
                if diameter > max_diameter: 
                    max_diameter = diameter  
                    max_frame_idx = i  

                cv2.drawContours(frame, [largest + [0, roi_top]], -1, (0, 255, 0), 2)

        diameters.append(diameter) 

        # Save frames for all four stages
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

    cap.release() 

# user manual selection of diamter
    if "Max Diameter" in selected_frames:
        def click_event(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN: 
                param.append((x, y))  
                cv2.circle(temp_frame, (x, y), 5, (0, 0, 255), -1) 
                cv2.imshow("Select Two Points", temp_frame)  # Update window to show circle

        temp_frame = selected_frames["Max Diameter"].copy() 
        points = []  
        cv2.imshow("Select Two Points", temp_frame) 
        cv2.setMouseCallback("Select Two Points", click_event, points)  

        while len(points) < 2: 
            cv2.waitKey(1)
        cv2.destroyWindow("Select Two Points") 

        # Calculate distance between two clicked points
        dx = points[0][0] - points[1][0]  
        dy = points[0][1] - points[1][1]  
        pixel_distance = (dx**2 + dy**2)**0.5  
        manual_diameter = pixel_distance * microns_per_pixel  

        if manual_diameter < 1.2 * nozzle_diameter:
            print("Warning: Selected droplet diameter is suspiciously close to nozzle diameter.")

        diameters[max_frame_idx] = manual_diameter 
        max_diameter = manual_diameter  

        pt1 = (int(points[0][0]), int(points[0][1])) 
        pt2 = (int(points[1][0]), int(points[1][1])) 
        cv2.line(selected_frames["Max Diameter"], pt1, pt2, (255, 0, 0), 2)

    return selected_frames, frame_indices, diameters, max_diameter, max_frame_idx
