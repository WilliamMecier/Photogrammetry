#This script was created by William Mecier for RESPEC
#
#This script is designed to take a folder of
#1. Drone imagery
#2. 3 shapefiles of the areas of interest for Civil 3D
#3. A DSM
#4. A DTM

#Import the necessary modules
import arcpy
from arcpy.sa import *
import time

#start timer
start_time = time.time()


# Check out the Spatial Analyst extension
#arcpy.CheckOutExtension("Spatial")

# Define input parameters
input_orthomosaic = arcpy.GetParameterAsText(0)
input_dsm = arcpy.GetParameterAsText(1)
input_dtm = arcpy.GetParameterAsText(2)
input_aois = arcpy.GetParameterAsText(3)  # AOIs are now a multi-value parameter and optional
output_location = arcpy.GetParameterAsText(4)
coordinate_system = arcpy.GetParameterAsText(5)
dwg_output_location = arcpy.GetParameterAsText(6)

# Process the AOIs if provided
aoi_list = input_aois.split(';') if input_aois else []

try:
    # Project the raster files
    projected_orthomosaic = arcpy.management.ProjectRaster(input_orthomosaic, output_location + "\\projected_orthomosaic.tif", coordinate_system)
    projected_dsm = arcpy.management.ProjectRaster(input_dsm, output_location + "\\projected_dsm.tif", coordinate_system)
    projected_dtm = arcpy.management.ProjectRaster(input_dtm, output_location + "\\projected_dtm.tif", coordinate_system)

    # Subtract DTM from DSM
    difference_raster = Minus(projected_dsm, projected_dtm)
    difference_raster.save(output_location + "\\dsm_minus_dtm.tif")

    # Export original DTM and DSM to CAD
    arcpy.ExportCAD_conversion([projected_dsm, projected_dtm], "DWG_R2018", dwg_output_location + "\\original_dsm_dtm.dwg", "USE_FILENAMES")

    # Check if any AOIs were provided
    if aoi_list:
        for index, aoi in enumerate(aoi_list):
            # Clip the raster files
            clipped_orthomosaic = arcpy.management.Clip(projected_orthomosaic, "#", output_location + f"\\clipped_orthomosaic_{index}.tif", aoi, "#", "NONE", "NO_MAINTAIN_EXTENT")
            clipped_dsm = arcpy.management.Clip(projected_dsm, "#", output_location + f"\\clipped_dsm_{index}.tif", aoi, "#", "NONE", "NO_MAINTAIN_EXTENT")
            clipped_dtm = arcpy.management.Clip(projected_dtm, "#", output_location + f"\\clipped_dtm_{index}.tif", aoi, "#", "NONE", "NO_MAINTAIN_EXTENT")

            # Generate contours
            contours_dsm_5ft = arcpy.3d.Contour(clipped_dsm, output_location + f"\\contours_dsm_5ft_{index}.shp", 5, 0)
            contours_dtm_5ft = arcpy.3d.Contour(clipped_dtm, output_location + f"\\contours_dtm_5ft_{index}.shp", 5, 0)
            contours_dsm_1ft = arcpy.3d.Contour(clipped_dsm, output_location + f"\\contours_dsm_1ft_{index}.shp", 1, 0)
            contours_dtm_1ft = arcpy.3d.Contour(clipped_dtm, output_location + f"\\contours_dtm_1ft_{index}.shp", 1, 0)

            # Export contours to CAD
            arcpy.ExportCAD_conversion([contours_dsm_5ft, contours_dtm_5ft, contours_dsm_1ft, contours_dtm_1ft], "DWG_R2018", dwg_output_location + f"\\contours_{index}.dwg", "USE_FILENAMES")

            # Export clipped AOIs to CAD (if they are feature layers or feature classes)
            if arcpy.Exists(aoi):
                arcpy.ExportCAD_conversion(aoi, "DWG_R2018", dwg_output_location + f"\\clipped_aoi_{index}.dwg", "USE_FILENAMES")

    arcpy.AddMessage("Processing completed successfully")

except Exception as e:
    arcpy.AddError(f"Error occurred: {str(e)}")

# Check in the Spatial Analyst extension
#arcpy.CheckInExtension("Spatial")

#end timer
end_time = time.time()
arcpy.AddMessage("Elapsed time: " + str(end_time - start_time) + " seconds")
