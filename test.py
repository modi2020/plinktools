#! /usr/bin/env python

# Copyright (c) 2013 Genome Research Ltd. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Iain Bancarz, ib5@sanger.ac.uk

import json, os, sys, unittest

from tempfile import mkdtemp
from plink import MafHetFinder, PlinkEquivalenceTester, PlinkMerger, \
    PlinkValidator
from checksum import ChecksumFinder

class TestPlink(unittest.TestCase):

    def setUp(self):
        self.dataDir = '/nfs/gapi/data/genotype/plinktools_test'
        self.outDir = os.path.abspath(mkdtemp(dir='.'))
        print "Output: "+self.outDir
        self.checksum = ChecksumFinder()
        self.validator = PlinkValidator()

    def test_equivalence(self):
        """Test equivalence check on pairs of datasets"""
        stem1 = os.path.join(self.dataDir, 'samples_part_100_small')
        stem2 = os.path.join(self.dataDir, 'samples_part_100_small')
        pet = PlinkEquivalenceTester()
        match = pet.compareBinary(stem1, stem2)
        self.assertTrue(match)
        stem3 = os.path.join(self.dataDir, 'samples_part_101_small')
        match = pet.compareBinary(stem1, stem3)
        self.assertFalse(match)

    def test_executables(self):
        """Check that executable scripts compile without crashing"""
        scripts = ['compare.py', 'het_by_maf.py', 'merge_bed.py']
        for script in scripts:
            status = os.system(script+' --help > /dev/null')
            self.assertEqual(status, 0)

    def test_maf_het(self):
        """Test het calculation on high/low maf"""
        stem = os.path.join(self.dataDir, 'samples_part_100_small')
        outJson = os.path.join(self.outDir, 'het_by_maf.json')
        outText = os.path.join(self.outDir, 'het_by_maf.txt')
        mhf = MafHetFinder()
        samples = 25
        snps = 538448
        countInfo = mhf.mafSplitHetCounts(stem+".bed", samples, snps)
        sampleNames = mhf.readSampleNames(stem+".fam")
        mhf.writeJson(outJson, countInfo, sampleNames, snps)
        md5 = self.checksum.getMD5hex(outJson)
        self.assertEqual(md5, '121d5568bfeac001ee04aa1860c333fe')
        mhf.writeText(outText, countInfo, samples, snps)
        md5 = self.checksum.getMD5hex(outText)
        self.assertEqual(md5, '594ab40eadf9e61f9599c477556d3ea4')

    def test_merge_congruent_samples(self):
        """Merge a set of 49 .bed datasets with 1162 samples
        
        Case of congruent samples, disjoint SNP sets"""
        stemListPath = os.path.join(self.dataDir, 'congruent_samples.json')
        stemList = json.loads(open(stemListPath).read())
        prefix = 'merge_congruent_sample_test'
        out = os.path.join(self.outDir, prefix+'_list')
        pm = PlinkMerger()
        pm.merge(stemList, out, verbose=False)
        md5 = self.checksum.getMD5hex(out+".bed")
        self.assertEqual(md5, '9931ab854c92e2efcffb48ec2480f2bb')
        self.assertTrue(self.validator.run(out))
        # same thing, but using glob instead of list to find inputs
        inputPrefix = os.path.join(self.dataDir, 'omnix_prcmd_20130624*')
        stemList = pm.findBedStems(inputPrefix)
        out = os.path.join(self.outDir, prefix+'_glob')
        pm.merge(stemList, out, verbose=False)
        md5 = self.checksum.getMD5hex(out+".bed")
        self.assertEqual(md5, '9931ab854c92e2efcffb48ec2480f2bb')
        self.assertTrue(self.validator.run(out))

    def test_merge_congruent_snps(self):
        """Merge two .bed datasets with 100 and 81 samples respectively
       
        Case of congruent SNP sets, disjoint samples
        Size of second dataset is not divisible by 4 -- tests recoding"""
        stem0 = os.path.join(self.dataDir, 'samples_part_000.smajor')
        stem1 = os.path.join(self.dataDir, 'samples_part_028.smajor')
        prefix = 'merge_congruent_snp_test'
        out = os.path.join(self.outDir, prefix)
        PlinkMerger().merge((stem0, stem1), out, verbose=False)
        self.assertTrue(os.path.exists(out+".bed"))
        md5 = self.checksum.getMD5hex(out+".bed")
        self.assertEqual(md5, 'db7dc2a92d339817d6d18974b0add3c7')
        self.assertTrue(self.validator.run(out))

if __name__ == "__main__":
    unittest.main(verbosity=2)
