# Prosys

Project Deployment System

## Command line interface

    Usage: prosys.py [options] module1 module2 tag1 tag2
    
    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -o DIRNAME, --out=DIRNAME
                            create or check project in DIRNAME
      -s, --src             move proj folder content to src folder
      -l, --list            show modules list
      -m, --macroses        show list or macroses to replace in files
      -i, --license         show list of available licenses
      -r, --replace         replace macroses in copyed template files
      -d, --disable         disable templates update
      -n, --no_results      do not show results
      -q, --quiet           silent mode

## Usage

Example:

    prosys -o test/proj base cpptools win32 ru_RU doxygen issues licenses MIT test@test.ru opensource pages setup tests version wiki

You can read more about usage in the project [Wiki](https://github.com/sigdev2/prosys/wiki).

## License

[Apache2](https://choosealicense.com/licenses/apache-2.0/)
