#!/usr/bin/env python

__description__ = 'Calculate byte statistics'
__author__ = 'Didier Stevens'
__version__ = '0.0.2'
__date__ = '2015/10/23'

"""
Source code put in public domain by Didier Stevens, no Copyright
https://DidierStevens.com
Use at your own risk

History:
  2014/10/25: start
  2014/10/26: refactoring
  2015/10/17: added buckets and properties
  2015/10/22: 0.0.2 added sequence detection
  2015/10/23: finished man

Todo:
"""

import optparse
import glob
import sys
import collections
import os
import math
import string
import textwrap
import binascii

def PrintManual():
    manual = '''
Manual:

byte-stats is a tool to calculate byte statistics of the content of files. It helps to determine the type or content of a file.

Let's start with some examples.
all.bin is a 256-byte large file, containing all possible byte values. The bytes are ordered: the first byte is 0x00, the second one is 0x01, the third one is 0x02, ... and the last one is 0xFF.

$byte-stats.py all.bin

Byte ASCII Count     Pct
0x00           1   0.39%
0x01           1   0.39%
0x02           1   0.39%
0x03           1   0.39%
0x04           1   0.39%
...
0xfb           1   0.39%
0xfc           1   0.39%
0xfd           1   0.39%
0xfe           1   0.39%
0xff           1   0.39%

Size: 256

                   File(s)
Entropy:           8.000000
NULL bytes:               1   0.39%
Control bytes:           27  10.55%
Whitespace bytes:         6   2.34%
Printable bytes:         94  36.72%
High bytes:             128  50.00%

First byte-stats.py will display a histogram of byte values found in the file(s). The first column is the byte value in hex (Byte), the second column is its ASCII value, third column tells us how many times the byte value appears (Count) and the last column is the percentage (Pct).
This histogram is sorted by Count (ascending). To change the order use option -d (descending), to sort by byte value use option -k (key).
By default, the first 5 and last 5 entries of the histogram are displayed. To display all values, use option -a (all).

After the histogram, the size of the file(s) is displayed.

Finally, the following statistics for the files(s) are displayed:
* Entropy (between 0.0 and 8.0).
* Number and percentage of NULL bytes (0x00).
* Number and percentage of Control bytes (0x01 through 0x1F, excluding whitespace bytes and including 0x7F).
* Number and percentage of Whitespace bytes (0x09 through 0x0D and 0x20).
* Number and percentage of Printable bytes (0x21 through 0x7E).
* Number and percentage of High bytes (0x80 through 0xFF).

byte-stats.py will also split the file in equally sized parts (called buckets) and perform the same calculations for these buckets. The default size of a bucket is 10KB (10240 bytes), but can be chosen with option -b (bucket). If the file is smaller than the bucket size, no bucket calculations are performed. If the file size is not an exact multiple of the bucket size, then no calculations are done for the last bucket (because it is incomplete).

Here is an example with buckets (file random.bin just contains random bytes):

$byte-stats.py random.bin

Byte ASCII Count     Pct
0xce         242   0.32%
0x14         248   0.33%
0x52 R       251   0.34%
0xba         251   0.34%
0x3e >       256   0.34%
...
0x2e .       332   0.44%
0x45 E       336   0.45%
0xc9         336   0.45%
0x1b         338   0.45%
0x75 u       344   0.46%

Size: 74752  Bucket size: 10240  Bucket count: 7

                   File(s)           Minimum buckets   Maximum buckets
Entropy:           7.997180          7.981543          7.984125
NULL bytes:             303   0.41%        34   0.33%        44   0.43%
Control bytes:         7888  10.55%      1046  10.21%      1117  10.91%
Whitespace bytes:      1726   2.31%       220   2.15%       254   2.48%
Printable bytes:      27278  36.49%      3680  35.94%      3812  37.23%
High bytes:           37557  50.24%      5096  49.77%      5211  50.89%

Besides the file size (74752), the size of the bucket (10240) and then number of buckets (7) is displayed.
And next to the entropy and byte counters for the complete file, the entropy and byte counters are calculated for each bucket. The minimum values for the bucket entropy and byte counters are displayed (Minimum buckets), and also the maximum values (Maximum buckets).
A significant difference between the overal statistics and bucket statistics can indicate a file that is not uniform in its content.
Like in this picture "encrypted" by ransomware:

$byte-stats.py picture.jpg.ransom

Byte ASCII Count     Pct
0x44 D      1172   0.13%
0x16        1310   0.15%
0x22 "      1371   0.16%
0xc2        1421   0.16%
0x17        1437   0.16%
...
0x7a z      7958   0.91%
0x82        8006   0.91%
0x7e ~      8571   0.98%
0x80       22232   2.53%
0x00       23873   2.72%

Size: 877456  Bucket size: 10240  Bucket count: 85

                   File(s)           Minimum buckets   Maximum buckets
Entropy:           7.815519          5.156678          7.981628
NULL bytes:           23873   2.72%         8   0.08%      1643  16.04%
Control bytes:        92243  10.51%        98   0.96%      1275  12.45%
Whitespace bytes:     16241   1.85%         1   0.01%       263   2.57%
Printable bytes:     303975  34.64%      2476  24.18%      5219  50.97%
High bytes:          441124  50.27%      3728  36.41%      6772  66.13%

The entropy for the file is 7.815519 (encrypted or compressed), but there is one part of the file (bucket) with an entropy of (5.156678). This part is not encrypted or compressed.
To locate this part, option -l (list) can be used to list the entropy values for each bucket:

$byte-stats.py -l picture.jpg.ransom

0x00000000 7.978380
0x00002800 7.979475
0x00005000 7.981628
0x00007800 7.267890
0x0000a000 6.579047
0x0000c800 6.798210
0x0000f000 6.733402
0x00011800 6.496882
0x00014000 5.743983
0x00016800 5.488550
0x00019000 5.156678
0x0001b800 5.330629
0x0001e000 6.057448
0x00020800 6.425884
0x00023000 6.880007
0x00025800 6.856647
...

The bucket starting at position 0x00019000 has the lowest entropy.

A list for the other properties (NULL bytes, ...) can be produced by using option -l together with option -p (property). For example options "-l -p n" will produce a list of the number of NULL bytes for each bucket.

Option -s (sequence) instructs byte-stats to search for simple byte sequences. A simple byte sequence is a sequence of bytes where the difference (unsigned) between 2 consecutive bytes is a constant.
Example:

$byte-stats.py -s picture.jpg.ransom

Byte ASCII Count     Pct
0x44 D      1172   0.13%
0x16        1310   0.15%
0x22 "      1371   0.16%
0xc2        1421   0.16%
0x17        1437   0.16%
...
0x7a z      7958   0.91%
0x82        8006   0.91%
0x7e ~      8571   0.98%
0x80       22232   2.53%
0x00       23873   2.72%

Size: 877456  Bucket size: 10240  Bucket count: 85

                   File(s)           Minimum buckets   Maximum buckets
Entropy:           7.815519          5.156678          7.981628
NULL bytes:           23873   2.72%         8   0.08%      1643  16.04%
Control bytes:        92243  10.51%        98   0.96%      1275  12.45%
Whitespace bytes:     16241   1.85%         1   0.01%       263   2.57%
Printable bytes:     303975  34.64%      2476  24.18%      5219  50.97%
High bytes:          441124  50.27%      3728  36.41%      6772  66.13%

Position    Length Diff Bytes
0x00013984:    246  128 0x8000800080008000800080008000800080008000...
0x00013c01:    206  128 0x0080008000800080008000800080008000800080...
0x0001b186:    205  128 0x8000800080008000800080008000800080008000...
0x0001b406:    205  128 0x8000800080008000800080008000800080008000...
0x0001b906:    204  128 0x8000800080008000800080008000800080008000...
0x0001bb86:    204  128 0x8000800080008000800080008000800080008000...
0x0001be06:    200  128 0x8000800080008000800080008000800080008000...
0x0001c086:    200  128 0x8000800080008000800080008000800080008000...
0x0001c306:    200  128 0x8000800080008000800080008000800080008000...
0x0001c586:    196  128 0x8000800080008000800080008000800080008000...

Position is the start of the detected sequence, Length is the number of bytes in the sequence, Diff is the difference (unsigned) between 2 consecutive bytes and Bytes displays the hex values of the start of the sequence.
By default, the 10 longest sequences are displayed. All sequences (minimum 3 bytes long) can be displayed with option -a.

Sequence detection is useful as an extra check when the entropy and byte counters indicate the file is random:

$byte-stats.py -s not-random.bin

Byte ASCII Count     Pct
0x00          16   0.39%
0x01          16   0.39%
0x02          16   0.39%
0x03          16   0.39%
0x04          16   0.39%
...
0xfb          16   0.39%
0xfc          16   0.39%
0xfd          16   0.39%
0xfe          16   0.39%
0xff          16   0.39%

Size: 4096

                   File(s)
Entropy:           8.000000
NULL bytes:              16   0.39%
Control bytes:          432  10.55%
Whitespace bytes:        96   2.34%
Printable bytes:       1504  36.72%
High bytes:            2048  50.00%

Position    Length Diff Bytes
0x00000000:   4096    1 0x000102030405060708090a0b0c0d0e0f10111213...
'''
    for line in manual.split('\n'):
        print(textwrap.fill(line, 79))

# CIC: Call If Callable
def CIC(expression):
    if callable(expression):
        return expression()
    else:
        return expression

# IFF: IF Function
def IFF(expression, valueTrue, valueFalse):
    if expression:
        return CIC(valueTrue)
    else:
        return CIC(valueFalse)

def File2Strings(filename):
    try:
        f = open(filename, 'r')
    except:
        return None
    try:
        return map(lambda line:line.rstrip('\n'), f.readlines())
    except:
        return None
    finally:
        f.close()

def ProcessAt(argument):
    if argument.startswith('@'):
        strings = File2Strings(argument[1:])
        if strings == None:
            raise Exception('Error reading %s' % argument)
        else:
            return strings
    else:
        return [argument]

def ExpandFilenameArguments(filenames):
    return list(collections.OrderedDict.fromkeys(sum(map(glob.glob, sum(map(ProcessAt, filenames), [])), [])))

def CalculateByteStatistics(dPrevalence):
    sumValues = sum(dPrevalence.values())
    countNullByte = dPrevalence[0]
    countControlBytes = 0
    countWhitespaceBytes = 0
    for iter in range(1, 0x21):
        if chr(iter) in string.whitespace:
            countWhitespaceBytes += dPrevalence[iter]
        else:
            countControlBytes += dPrevalence[iter]
    countControlBytes += dPrevalence[0x7F]
    countPrintableBytes = 0
    for iter in range(0x21, 0x7F):
        countPrintableBytes += dPrevalence[iter]
    countHighBytes = 0
    for iter in range(0x80, 0x100):
        countHighBytes += dPrevalence[iter]
    entropy = 0.0
    for iter in range(0x100):
        if dPrevalence[iter] > 0:
            prevalence = float(dPrevalence[iter]) / float(sumValues)
            entropy += - prevalence * math.log(prevalence, 2)
    return sumValues, entropy, countNullByte, countControlBytes, countWhitespaceBytes, countPrintableBytes, countHighBytes

def GenerateLine(prefix, counter, sumValues, buckets, index, options):
    line = '%-18s%9d %6.2f%%' % (prefix + ':', counter, float(counter) / sumValues * 100.0)
    if len(buckets) > 0:
        value = min([properties[index] for position, properties in buckets])
        line += ' %9d %6.2f%%' % (value, float(value) / float(options.bucket) * 100.0)
        if len(buckets) > 1:
            value = max([properties[index] for position, properties in buckets])
            line += ' %9d %6.2f%%' % (value, float(value) / float(options.bucket) * 100.0)
    return line

def TruncateString(string, length):
   if len(string) > length:
       return string[:length] + '...'
   else:
       return string

def ByteSub(byte1, byte2):
    diff = byte1 - byte2
    if diff < 0:
        diff += 256
    return diff

def ByteStats(args, options):
    if options.bucket < 1:
        print('Bucket size must be at least 1, not %d' % options.bucket)
        return
    countBytes = 0
    dPrevalence = {iter: 0 for iter in range(0x100)}
    dPrevalenceBucket = {iter: 0 for iter in range(0x100)}
    buckets = []
    diffs = []
    values = []
    dDiffs = {}
    if args != ['']:
        args = ExpandFilenameArguments(args)
    for file in args:
        if file == '':
            fIn = sys.stdin
            if sys.platform == 'win32':
                import msvcrt
                msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        else:
            fIn = open(file, 'rb')
        for char in fIn.read():
            value = ord(char)
            dPrevalence[value] += 1
            dPrevalenceBucket[value] += 1
            countBytes += 1
            if options.sequence:
                values.append(value)
                if countBytes > 1:
                    diff = ByteSub(value, values[-2])
                    if diffs == []:
                        diffs = [diff]
                        savPosition = countBytes
                    elif diffs[-1] == diff:
                        diffs.append(diff)
                    else:
                        if len(diffs) > 1:
                            dDiffs[savPosition - 2] = values[:-1]
                        diffs = [diff]
                        values = values[-2:]
                        savPosition = countBytes
            if countBytes % options.bucket == 0:
                buckets.append([countBytes - options.bucket, CalculateByteStatistics(dPrevalenceBucket)])
                dPrevalenceBucket = {iter: 0 for iter in range(0x100)}
        if fIn != sys.stdin:
            fIn.close()
    if len(diffs) > 1:
        dDiffs[savPosition - 2] = values

    if countBytes == 0:
        print('Empty file(s)! Statistics can not be calclated.')
        return

    sumValues, entropy, countNullByte, countControlBytes, countWhitespaceBytes, countPrintableBytes, countHighBytes = CalculateByteStatistics(dPrevalence)

    #  Calculate per bucket entropy
    dProperties = {'e': 1, 'n': 2, 'c': 3, 'w': 4, 'p': 5, 'h': 6}
    if options.property not in dProperties:
        print('Unknown property: %s' % options.property)
        return
    index = dProperties[options.property]
    if options.property == 'e':
        format = '0x%08x %f'
    else:
        format = '0x%08x %9d'
    perBucketEntropy = []
    for position, properties in buckets:
        perBucketEntropy.append(properties[index])

    # Calculate average and variance of entropies
    listCount = dPrevalence.items()
    if options.keys:
        index = 0
    else:
        index = 1
    listCount.sort(lambda x, y:cmp(x[index], y[index]), reverse=options.descending)
    lineCounter = 0
    dotsPrinted = False
    # print('Byte ASCII Count     Pct')
    for key, value in listCount:
        if options.all or lineCounter < 5 or lineCounter > 250:
            line = '0x%02x %s %9d %6.2f%%' % (key, IFF(key >= 0x20 and key < 0x7F, chr(key), ' '), value, float(value) / sumValues * 100.0)
            # print(line)
        elif not dotsPrinted:
            # print('...')
            dotsPrinted = True
        lineCounter +=  1
    # print('')
    line = 'Size: %d' % sumValues
    if len(buckets) > 0:
        line += '  Bucket size: %d  Bucket count: %d' % (options.bucket, len(buckets))
    # print(line)
    # print('')
    line = '                   File(s)'
    if len(buckets) == 1:
        line += '           Bucket'
    elif len(buckets) > 1:
        line += '           Minimum buckets   Maximum buckets'
    # print(line)
    line = 'Entropy:           %f' % entropy
    
    def GetBucketVariance(data):   
        n = len(data)
        if(n <= 0):
            return 0
        mean = sum(data) / n
        deviations = [(x - entropy) ** 2 for x in data]
            
        variance = sum(deviations) / n
        return variance
    data = [properties[1] for _, properties in buckets]
    line += '    %f' % GetBucketVariance(data)

    if len(buckets) > 0:
        line += '          %f' % min([properties[1] for position, properties in buckets])
        if len(buckets) > 1:
            line += '          %f' % max([properties[1] for position, properties in buckets])
    # print(GenerateLine('NULL bytes', countNullByte, sumValues, buckets, 2, options))
    # print(GenerateLine('Control bytes', countControlBytes, sumValues, buckets, 3, options))
    # print(GenerateLine('Whitespace bytes', countWhitespaceBytes, sumValues, buckets, 4, options))
    # print(GenerateLine('Printable bytes', countPrintableBytes, sumValues, buckets, 5, options))
    # print(GenerateLine('High bytes', countHighBytes, sumValues, buckets, 6, options))
    result = line.split()  
    result.append(perBucketEntropy)
    return result

    # if options.sequence:
    #     print('')
    #     print('Position    Length Diff Bytes')
    #     sequences = sorted(dDiffs.items(), cmp=lambda x, y: IFF(len(x[1]) == len(y[1]), cmp(y[0], x[0]), cmp(len(x[1]), len(y[1]))), reverse=True)
    #     if not options.all:
    #         sequences = sequences[:10]
    #     for sequence in sequences:
    #         print('0x%08x: %6d %4d 0x%s' % (sequence[0], len(sequence[1]), ByteSub(sequence[1][1], sequence[1][0]), TruncateString(binascii.hexlify(''.join([chr(c) for c in sequence[1]])), 40)))

def CalculateEntropy(file):
    moredesc = '''

files:
wildcards are supported
@file: run command on each file listed in the text file specified

Source code put in the public domain by Didier Stevens, no Copyright
Use at your own risk
https://DidierStevens.com'''

    oParser = optparse.OptionParser(usage='usage: %prog [options] [files ...]\n' + __description__ + moredesc, version='%prog ' + __version__)
    oParser.add_option('-m', '--man', action='store_true', default=False, help='Print manual')
    oParser.add_option('-d', '--descending', action='store_true', default=False, help='Sort descending')
    oParser.add_option('-k', '--keys', action='store_true', default=False, help='Sort on keys in stead of counts')
    oParser.add_option('-b', '--bucket', type=int, default=10240, help='Size of bucket (default is 10240 bytes)')
    oParser.add_option('-l', '--list', action='store_true', default=False, help='Print list of bucket property')
    oParser.add_option('-p', '--property', default='e', help='Property to list: encwph')
    oParser.add_option('-a', '--all', action='store_true', default=False, help='Print all byte stats')
    oParser.add_option('-s', '--sequence', action='store_true', default=False, help='Detect simple sequences')
    (options, args) = oParser.parse_args()

    if options.man:
        oParser.print_help()
        PrintManual()
        return

    if len(args) == 0:
        args = ['']
    return ByteStats([file], options)

if __name__ == '__main__':
    # Run it as python2 calc_stats.py path_to_file
    line = CalculateEntropy(sys.argv[1])
    print(line)