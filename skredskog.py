import arcpy
from arcpy import env
from arcpy.sa import *
import os


def check_bookmark(bkmk):
    ok = False
    for m in aprx.listMaps():
        for i in m.listBookmarks():
            if i.name == bkmk:
                ok = True
                break
    if ok == False:
        arcpy.AddError('Bookmark ble ikke funnet.')
        exit()


def _to_bookmark(bkmk):
    for m in aprx.listMaps():
        for i in m.listBookmarks():
            if i.name == bkmk:
                if isinstance(aprx.activeView, arcpy._mp.Layout) == True:
                    for j in range(len(aprx.listLayouts())):
                        if aprx.activeView.name == aprx.listLayouts()[j].name:
                            mf = aprx.listLayouts()[j].listElements('MAPFRAME_ELEMENT')[0]
                            mf.zoomToBookmark(i)
                            extent = mf.camera.getExtent()
                            return extent
                else:
                    mv = aprx.activeView
                    mv.zoomToBookmark(i)
                    extent = mv.camera.getExtent()
                    arcpy.AddMessage(extent)
                    return extent

def delete_files(file_list):
    """Delete files if they exist."""
    for file_path in file_list:
        if arcpy.Exists(file_path):
            arcpy.management.Delete(file_path)
            print(f"Deleted: {file_path}")
        elif os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted (OS): {file_path}")
        else:
            print(f"Not found (skipped): {file_path}")


if __name__ == '__main__':
    arcpy.CheckOutExtension("Spatial")

    aprx = arcpy.mp.ArcGISProject("CURRENT")
    project_folder = os.path.dirname(aprx.filePath)

    bkmk = arcpy.GetParameterAsText(0)
    check_bookmark(bkmk)
    extent = _to_bookmark(bkmk)

    arcpy.env.workspace = os.path.join(project_folder, "Skog")
    arcpy.env.overwriteOutput = True

    files_to_delete = [
    'Kronedekning_klippet.tif',
    'Treslag_klippet.tif',
    "Kronedekning_Lauvskog_Ideell.tif",
    "Kronedekning_Barskog_Ideell.tif",
    "Treslag_Gran.tif",
    "Treslag_Furu.tif",
    "Treslag_Lauv.tif",
    "Treslag_Gran_og_Furu.tif",
    "Innvirkende_barskog.tif",
    "Innvirkende_lauvskog.tif",
    "Innvirkende_skog_mellomregning.tif",
    "Terrenghelning.tif",
    "Terrenghelning_over20.tif",
    "Innvirkende_skog_Losneomrode_mellomregning.tif",
    "Innvirkende_skog_mellomregning2.tif",
    "Innvirkende_skog_mellomregning.tif",
    "Innvirkende_skog_Losneomrode_mellomregning2.tif",
    "Innvirkende_skog_Losneomrode.tif",
    "Innvirkende_skog.tif",
    "Innvirkende_skog_mellomregning.shp",
    "Innvirkende_skog.shp",
    "Innvirkende_skog_Losneomrode_mellomregning.shp",
    "Innvirkende_skog_Losneomrode.shp"
    ]

    delete_files(files_to_delete)

    kronedek = arcpy.GetParameterAsText(1)
    krone_raster = Raster(kronedek)
    krone = ExtractByRectangle(krone_raster, extent)
    krone_output = os.path.join(arcpy.env.workspace, 'Kronedekning_klippet.tif')
    krone.save(krone_output)

    treslag = arcpy.GetParameterAsText(2)
    tre_raster = Raster(treslag)
    tre = ExtractByRectangle(tre_raster, extent)
    tre_output = os.path.join(arcpy.env.workspace, 'Treslag_klippet.tif')
    tre.save(tre_output)

    # Bruk RASTER CALCULATOR
    # Lauvskog-Ideell
    lauv_ideell = Con(krone >= 80, krone)
    lauv_ideell.save("Kronedekning_Lauvskog_Ideell.tif")

    # Barskog-Ideell
    bar_ideell = Con(krone >= 50, krone)
    bar_ideell.save("Kronedekning_Barskog_Ideell.tif")

    # Treslag-Gran
    gran = Con(tre == 1, 1)
    gran.save("Treslag_Gran.tif")

    # Treslag-Furu
    furu = Con(tre == 2, 2)
    furu.save("Treslag_Furu.tif")

    # Treslag-Lauv
    lauv = Con(tre == 3, 3)
    lauv.save("Treslag_Lauv.tif")

    # Bruk MOSAIC TO NEW RASTER
    # Input: Treslag_Furu, Treslag_Gran
    # Output: Treslag_Gran_og_Furu
    arcpy.MosaicToNewRaster_management(
        input_rasters=["Treslag_Furu.tif", "Treslag_Gran.tif"],
        output_location=arcpy.env.workspace,
        raster_dataset_name_with_extension="Treslag_Gran_og_Furu.tif",
        pixel_type="32_BIT_FLOAT",
        cellsize="",
        number_of_bands=1,
        mosaic_method="MAXIMUM"
    )


    # Bruk PLUS funksjon
    # Input 1: Kronedekning_Barskog_Ideell
    # Input 2: Treslag_Gran_og_Furu
    # Output: Kombinert_kronedekning_ideell_barskog.tif
    kombinert_barskog = Plus("Kronedekning_Barskog_Ideell.tif", "Treslag_Gran_og_Furu.tif")
    kombinert_barskog.save("Innvirkende_barskog.tif")

    # Tilsvarende metodikk for Lauvskog:
    # PLUS
    # Input 1: Kronedekning_Lauvskog_Ideell
    # Input 2: Treslag_Lauv
    # Output: Kombinert_kronedekning_ideell_lauvskog.tif
    kombinert_lauv = Plus("Kronedekning_Lauvskog_Ideell.tif", "Treslag_Lauv.tif")
    kombinert_lauv.save("Innvirkende_lauvskog.tif")

    # Bruk MOSAIC TO NEW RASTER
    # Input: Innvirkning_barskog, Innvirkning_lauvskog
    # Output: Innvirkning_skog
    arcpy.MosaicToNewRaster_management(
        input_rasters=["Innvirkende_barskog.tif", "Innvirkende_lauvskog.tif"],
        output_location=arcpy.env.workspace,
        raster_dataset_name_with_extension="Innvirkende_skog_mellomregning.tif",
        pixel_type="32_BIT_FLOAT",
        cellsize="",
        number_of_bands=1,
        mosaic_method="MAXIMUM"
    )


    #Kjør slope på terrengmodell med oppløysning 16x16
    # Cellsize er grovt, men gir ca. omfang av justering
    # Cellsize: Same as Skog_innverknad_skredfore
    terrengmodell = arcpy.GetParameterAsText(3)
    slope_output = Slope(terrengmodell, "DEGREE")
    slope_output.save("Terrenghelning.tif")

    #Raster Calculator >= 20
    # Input: Terrengshelling_Prosjekt_Stordat
    # Output: Terrengshelling_Prosjekt_Stordat_brattereEnn20.tif
    bratt = Con(slope_output >= 20, slope_output)
    bratt.save("Terrenghelning_over20.tif")

    # Bruk PLUS
    # Input 1: Skog_innverknad_skredfore
    # Input 2: Terrengshelling [...] brattereEnn20
    # Output: Skog_innverknad_Losneomrayn.tif
    skog_innverknad = Raster("Innvirkende_skog_mellomregning.tif")
    skog_losne = Plus(skog_innverknad, bratt)
    skog_losne.save("Innvirkende_skog_Losneomrode_mellomregning.tif")

    in_raster = Raster("Innvirkende_skog_mellomregning.tif")
    out_raster = (in_raster * 0) + 1
    out_raster.save("Innvirkende_skog_mellomregning2.tif")

    in_raster = Raster("Innvirkende_skog_Losneomrode_mellomregning.tif")
    out_raster = (in_raster * 0) + 1
    out_raster.save("Innvirkende_skog_Losneomrode_mellomregning2.tif")

    in_raster = Raster("Innvirkende_skog_Losneomrode_mellomregning2.tif")
    out_int = Int(in_raster)
    out_int.save("Innvirkende_skog_Losneomrode.tif")

    in_raster = Raster("Innvirkende_skog_mellomregning2.tif")
    out_int = Int(in_raster)
    out_int.save("Innvirkende_skog.tif")

    arcpy.CheckOutExtension("Cartography")

    raster_input = "Innvirkende_skog.tif"
    polygon_output = "Innvirkende_skog_mellomregning.shp"
    polygon_smoothed = "Innvirkende_skog.shp"

    arcpy.RasterToPolygon_conversion(
        in_raster=raster_input,
        out_polygon_features=polygon_output,
        simplify="NO_SIMPLIFY",
        raster_field="VALUE"
    )

    arcpy.SmoothPolygon_cartography(
        in_features=polygon_output,
        out_feature_class=polygon_smoothed,
        algorithm="PAEK",
        tolerance=32,
    )

    raster_input = "Innvirkende_skog_Losneomrode.tif"
    polygon_output = "Innvirkende_skog_Losneomrode_mellomregning.shp"
    polygon_smoothed = "Innvirkende_skog_Losneomrode.shp"

    arcpy.RasterToPolygon_conversion(
        in_raster=raster_input,
        out_polygon_features=polygon_output,
        simplify="NO_SIMPLIFY",
        raster_field="VALUE"
    )

    arcpy.SmoothPolygon_cartography(
        in_features=polygon_output,
        out_feature_class=polygon_smoothed,
        algorithm="PAEK",
        tolerance=32,
    )

    arcpy.AddMessage("Prosessering fullført, dine filer ligger i mappen SKOG i prosjektmappen.")






