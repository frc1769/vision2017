import cv2
import numpy
import math
from enum import Enum

class GripPipeline:
    """
    An OpenCV pipeline generated by GRIP.
    """
    
    def __init__(self, width, height):
        """initializes all values to presets or None if need to be set
        """

        self.width = width
        self.height = height

        self.__cv_resize_dsize = (0, 0)
        self.__cv_resize_fx = 0.5
        self.__cv_resize_fy = 0.5
        self.__cv_resize_interpolation = cv2.INTER_LINEAR

        self.cv_resize_output = None

        self.__hsv_threshold_input = self.cv_resize_output
        self.__hsv_threshold_hue = [120,150]
        self.__hsv_threshold_saturation = [0, 255]
        self.__hsv_threshold_value = [145,255]

        self.hsv_threshold_output = None

        self.__cv_erode_src = self.hsv_threshold_output
        self.__cv_erode_kernel = None
        self.__cv_erode_anchor = (-1, -1)
        self.__cv_erode_iterations = 1
        self.__cv_erode_bordertype = cv2.BORDER_CONSTANT
        self.__cv_erode_bordervalue = (-1)

        self.cv_erode_output = None

        self.__mask_input = self.cv_resize_output
        self.__mask_mask = self.cv_erode_output

        self.mask_output = None

        self.__find_blobs_input = self.mask_output
        self.__find_blobs_min_area = 5.0
        self.__find_blobs_circularity = [0.0, 1.0]
        self.__find_blobs_dark_blobs = False

        self.find_blobs_output = None

        self.__find_lines_input = self.mask_output

        self.find_lines_output = None


    def process(self, source0):
        """
        Runs the pipeline and sets all outputs to new values.
        """
        # Step CV_resize0:
        self.__cv_resize_src = source0
        (self.cv_resize_output) = self.__cv_resize(self.__cv_resize_src, self.__cv_resize_dsize, self.__cv_resize_fx, self.__cv_resize_fy, self.__cv_resize_interpolation)

        # Step HSV_Threshold0:
        self.__hsv_threshold_input = self.cv_resize_output
        (self.hsv_threshold_output) = self.__hsv_threshold(self.__hsv_threshold_input, self.__hsv_threshold_hue, self.__hsv_threshold_saturation, self.__hsv_threshold_value)

        ## Step CV_erode0:
        #self.__cv_erode_src = self.hsv_threshold_output
        #(self.cv_erode_output) = self.__cv_erode(self.__cv_erode_src, self.__cv_erode_kernel, self.__cv_erode_anchor, self.__cv_erode_iterations, self.__cv_erode_bordertype, self.__cv_erode_bordervalue)

        # Step Mask0:
        self.__mask_input = self.cv_resize_output
        self.__mask_mask = self.hsv_threshold_output
        (self.mask_output) = self.__mask(self.__mask_input, self.__mask_mask)

        ## Step Find_Blobs0:
        self.__find_blobs_input = self.mask_output
        (self.find_blobs_output) = self.__find_blobs(self.__find_blobs_input, self.__find_blobs_min_area, self.__find_blobs_circularity, self.__find_blobs_dark_blobs)
        #print dir(self.find_blobs_output)
        #print '['
        #for x in self.find_blobs_output:
        #    print x.pt[0], x.pt[1], x.size
        #print ']'
        
        ## Step Find_Lines0:
        #self.__find_lines_input = self.mask_output
        #(self.find_lines_output) = self.__find_lines(self.__find_lines_input)

        x_sum = 0
        y_sum = 0
        size_sum = 0
        ct_pts = 0
        for p in self.find_blobs_output:
            ct_pts += 1
            x_sum += p.pt[0]
            y_sum += p.pt[1]
            size_sum += p.size
        if ct_pts:    
            x_val = x_sum / ct_pts / (self.width * self.__cv_resize_fx) * 2 - 1
            y_val = y_sum / ct_pts / (self.height * self.__cv_resize_fy) * 2 - 1
            size_val = size_sum / ct_pts / self.width
            print x_val, y_val, size_val, ct_pts
        else:
            x_val = 0
            y_val = 0
            size_val = 0

        
        return ( self.mask_output, ( x_val, y_val, size_val, ct_pts) )


    @staticmethod
    def __cv_resize(src, d_size, fx, fy, interpolation):
        """Resizes an Image.
        Args:
            src: A numpy.ndarray.
            d_size: Size to set the image.
            fx: The scale factor for the x.
            fy: The scale factor for the y.
            interpolation: Opencv enum for the type of interpolation.
        Returns:
            A resized numpy.ndarray.
        """
        return cv2.resize(src, d_size, fx=fx, fy=fy, interpolation=interpolation)

    @staticmethod
    def __hsv_threshold(input, hue, sat, val):
        """Segment an image based on hue, saturation, and value ranges.
        Args:
            input: A BGR numpy.ndarray.
            hue: A list of two numbers the are the min and max hue.
            sat: A list of two numbers the are the min and max saturation.
            lum: A list of two numbers the are the min and max value.
        Returns:
            A black and white numpy.ndarray.
        """
        out = cv2.cvtColor(input, cv2.COLOR_BGR2HSV)
        return cv2.inRange(out, (hue[0], sat[0], val[0]),  (hue[1], sat[1], val[1]))

    @staticmethod
    def __cv_erode(src, kernel, anchor, iterations, border_type, border_value):
        """Expands area of lower value in an image.
        Args:
           src: A numpy.ndarray.
           kernel: The kernel for erosion. A numpy.ndarray.
           iterations: the number of times to erode.
           border_type: Opencv enum that represents a border type.
           border_value: value to be used for a constant border.
        Returns:
            A numpy.ndarray after erosion.
        """
        return cv2.erode(src, kernel, anchor, iterations = (int) (iterations +0.5),
                            borderType = border_type, borderValue = border_value)

    @staticmethod
    def __mask(input, mask):
        """Filter out an area of an image using a binary mask.
        Args:
            input: A three channel numpy.ndarray.
            mask: A black and white numpy.ndarray.
        Returns:
            A three channel numpy.ndarray.
        """
        return cv2.bitwise_and(input, input, mask=mask)

    @staticmethod
    def __find_blobs(input, min_area, circularity, dark_blobs):
        """Detects groups of pixels in an image.
        Args:
            input: A numpy.ndarray.
            min_area: The minimum blob size to be found.
            circularity: The min and max circularity as a list of two numbers.
            dark_blobs: A boolean. If true looks for black. Otherwise it looks for white.
        Returns:
            A list of KeyPoint.
        """
        params = cv2.SimpleBlobDetector_Params()
        params.filterByColor = 1
        params.blobColor = (0 if dark_blobs else 255)
        params.minThreshold = 10
        params.maxThreshold = 220
        params.filterByArea = True
        params.minArea = min_area
        params.filterByCircularity = True
        params.minCircularity = circularity[0]
        params.maxCircularity = circularity[1]
        params.filterByConvexity = False
        params.filterByInertia = False
        detector = cv2.SimpleBlobDetector(params)
        return detector.detect(input)

    class Line:

        def __init__(self, x1, y1, x2, y2):
            self.x1 = x1
            self.y1 = y1
            self.x2 = x2
            self.y2 = y2

        def length(self):
            return numpy.sqrt(pow(self.x2 - self.x1, 2) + pow(self.y2 - self.y1, 2))

        def angle(self):
            return math.degrees(math.atan2(self.y2 - self.y1, self.x2 - self.x1))
    @staticmethod
    def __find_lines(input):
        """Finds all line segments in an image.
        Args:
            input: A numpy.ndarray.
        Returns:
            A filtered list of Lines.
        """
        detector = cv2.createLineSegmentDetector()
        if (len(input.shape) == 2 or input.shape[2] == 1):
            lines = detector.detect(input)
        else:
            tmp = cv2.cvtColor(input, cv2.COLOR_BGR2GRAY)
            lines = detector.detect(tmp)
        output = []
        if len(lines) != 0:
            for i in range(1, len(lines[0])):
                tmp = GripPipeline.Line(lines[0][i, 0][0], lines[0][i, 0][1],
                                lines[0][i, 0][2], lines[0][i, 0][3])
                output.append(tmp)
        return output



