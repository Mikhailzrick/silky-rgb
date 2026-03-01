#!/bin/bash

# Determine python site-package folder
PYTHON_PATH=$(python -c "import sys; print('\n'.join(sys.path))" | grep site-packages)
SILKY_RGB_PATH="$PYTHON_PATH/silkyrgb"

# Remove a previous installation of Silky RGB
if [ -d "$SILKY_RGB_PATH" ]; then
  echo "Removing previous Silky RGB installation from $SILKY_RGB_PATH"
  rm -Rf $SILKY_RGB_PATH;
fi

# Install Silky RGB
echo "Installing Silky RGB in $SILKY_RGB_PATH"

mkdir $SILKY_RGB_PATH
cp ../*.py               $SILKY_RGB_PATH
cp -r ../__pycache__     $SILKY_RGB_PATH
cp -r ../device_configs  $SILKY_RGB_PATH
cp -r ../drivers         $SILKY_RGB_PATH
cp -r ../effects         $SILKY_RGB_PATH

chmod +x "$SILKY_RGB_PATH"/*.py
chmod +x "$SILKY_RGB_PATH"/drivers/*.py
chmod +x "$SILKY_RGB_PATH"/effects/*.py
chmod +x "$SILKY_RGB_PATH"/effects/modes/*.py
chmod +x "$SILKY_RGB_PATH"/effects/notifications/*.py

knulli-save-overlay

echo "Restarting Silky RGB daemon"
/etc/init.d/S25silky-rgb restart
