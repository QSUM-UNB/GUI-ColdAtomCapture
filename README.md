# GUI-ColdAtomCapture
A PyQt graphical user interface for capturing time-of-flight images of cold atoms and analyzing their features.

## Requirements

The program is verified to be working on macOS 14 and 15 as well as Windows 11. The program *should* theoretically work on Linux, though your mileage may vary.

In order to use the program, you must be running Python version 3.10. This can be obtained [here.](https://python.org)

There are also some packages required from PIP. Ensure the following is installed:

|Packages|
|--------|
|PyQt6|
|Matplotlib|
|numpy|
|opencv-python|
|lmfit|

Finally, make sure that you have the Flir Spinnaker SDK installed along with the appropriate version of PySpin for Python 3.10 (this should either be bundled with or on the website for Spinnaker SDK). Further instructions can be found [here.](https://www.flir.ca/products/spinnaker-sdk/)

## Usage

The program can be run by invoking:

```sh
python3.10 app.py
```

You may also replace `python3.10` with whichever keyword you have bound to Python 3.10.