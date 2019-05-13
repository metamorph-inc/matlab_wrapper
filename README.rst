matlab_wrapper
==============

MATLAB Wrapper allows use of MATLAB scripts
and functions in the context of an OpenMDAO 1.x Problem.
There are two types of MATLAB scripts that can be integrated:
*Function Files* and *Bare Files*. The MATLAB Wrapper
determines the type by examining the script file.

Currently, only MATLAB version 2015a and later are supported.

Function Files
--------------

In a *Function File* you define a function with the same name as
the script filename and this becomes the entry point for the script.
There are a few restrictions in the current implementation:

-  Only scalar (double) type values are allowed as inputs and outputs.
-  There can be more than one function declared in the script, but the
   wrapper will only use as an entry point the function with the same
   name as the script filename. This name is case-sensitive and must
   match exactly.

Below is a *Function File* example of a MATLAB Wrapper script:

.. code-block:: matlab
   :caption: Example.m
   :name: Example.m

   function [sum, product] = Example(x, y, z)
   sum = x + y + z
   product = x * y * z
   end


Bare Files
----------

In a Bare File you define the inputs and outputs of the script by a
set of specially-formatted comments at the beginning of the file.
These comments allow you to define the data type of all the inputs
and outputs.

Below is a *Bare File* example of a script that doubles a number
of different types of inputs:

.. code-block:: matlab
   :caption: Double.m
   :name: Double.m

   % variable: output1 double output
   % variable: output2 double[] output
   % variable: output3 string output
   % variable: output4 string[] output
   % variable: input1 double input
   % variable: input2 double[] input
   % variable: input3 string input
   % variable: input4 string[] input

   output1 = input1 * 2
   output2 = input2 * 2
   output3 = strcat(input3, input3)
   output4 = [input4, input4]

You cannot define functions in a *Bare File* style MATLAB integration file;
however, you can call other function files that you have defined.


MATLAB Data Type Conversion
~~~~~~~~~~~~~~~~~~~~~~~~~~~

OpenMETA uses the Python `OpenMDAO <http://www.openmdao.org/>`_
framework to execute PETs. Since the data passed between analysis
blocks is managed by Python, the table below describes the conversions
that occur when data is passed into or out of a MATLAB Wrapper block.

=========================  ======================  =========================
Python                     to MATLAB               to Python
=========================  ======================  =========================
Boolean                    Logical                 Boolean
Int                        N/A [1]_
List of Ints               N/A [1]_
Numpy Int Array            Double Array            Numpy Float Array [2]_
Float                      Double                  Float [3]_
List of Floats             N/A [1]_
Numpy Float Array          Double Array            Numpy Float Array
String                     N/A [1]_
List of Strings            Cell Array of Strings   List of Strings
Numpy Array of Strings     N/A [1]_
Unicode                    Char                    Unicode
List of Unicodes           Cell Array of Unicodes  List of Unicodes
Dictionary                 Struct                  Dictionary [4]_
=========================  ======================  =========================

.. [1] These types are not allowed to be passed into MATLAB Wrapper analysis
   blocks.

.. [2] Integers in an array will be converted to floats upon passing through
   a MATLAB Wrapper analysis block.

.. [3] All doubles in MATLAB are essentially a one-by-one array
   (1x1), so the framework automatically unwraps all one-by-one arrays to
   a single float value as they are passed to the next analysis block.
   E.g. A 1x1 Numpy Array will become a double in MATLAB and will result in a
   double in OpenMDAO when it is passed to the next analysis block.

.. [4] Structs in MATLAB can only accept fieldnames that meet the following
   three criteria:

   #. Start with a letter
   #. Contain only letters, numbers, and/or the underscore character
   #. Must be no longer than ``namelengthmax`` (currently 63) characters

   Although Python can handle arbitrary strings as the keys in dictionaries,
   you must meet these criteria if you are going to pass the dictionaries
   to a MATLAB Wrapper block.

For examples of the conversion see the "MatlabConversions" PET in the
`Analysis Blocks <https://github.com/metamorph-inc/openmeta-examples-and-templates/tree/master/analysis-blocks>`_
project in the
`OpenMETA Examples And Templates <https://github.com/metamorph-inc/openmeta-examples-and-templates>`_
repository.
