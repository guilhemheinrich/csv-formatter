# /*
#  * ******************************************************************************
#  *                                     env-setup-conda.sh
#  *  csvformatter
#  *  Copyright © INRA 2019
#  *  Creation date:  06 February, 2019
#  *  Contact: arnaud.charleroy@inra.fr
#  * ******************************************************************************
#  */

nameEnv=csvFormater

conda create --name ${nameEnv} python=3.6 --yes
conda install --name ${nameEnv} pip

# using pip inside our environment : conda doesn't handle well the dependencies/version without gpu
# pip reference here the envornment version, so don't use pip3
conda activate ${nameEnv}
pip install --upgrade pip
pip install pyyaml
pip install pylint

echo "Use conda activate: ${nameEnv} or conda deactivate to get out of this environnment"
