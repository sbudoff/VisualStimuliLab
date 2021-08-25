# VisualStimuliLab
The Visual Stimuli Lab is a GUI created for the Poleg-Polsky lab as part of NRSC7657. This tool allows one with little coding experience to display arbitrary visual stimuli to light responsive cells and record their optical responses.

The VSL will search for an "Assets" folder in the same directory as itself. In this directory, it will search for a "Stimuli" directory. To change the available stimuli, simply add a subdirectory containing tiff files named in the order of desired video presentation.

As of 08/25/2021, several bugs are known to exist which will be addressed shortly.
1) The quick save features related to the ROIs are disabled
2) The frame rate suffers proportionately to the number of ROIs
3) When erasing an individual ROI, a reference to it persists in the available ROIs, to clear this, use the "Erase All" button
4) PySimpleGUI does not yet provide a transparent fill color for graph objects, thus to move an ROI only the border can be interacted with.
