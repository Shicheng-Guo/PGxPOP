"""
Greg McInes
Altman Lab
gmcinnes@stanford.edu
"""

import os
import argparse

# import multiprocessing as mp
import numpy as np

from timeit import default_timer as timer
from datetime import timedelta

import Gene
from DawgToys import welcome_message, get_vcf_subject_ids
from GenotypeParser import GenotypeParser
from DiplotypeCaller import *


class CityDawg(object):
    def __init__(self, vcf, gene, phased=False, build='grch38', debug=False, batch_mode=False):
        self.vcf = vcf
        self.gene = gene
        self.phased = phased
        self.build = build
        self.debug = debug
        self.batch_mode = batch_mode
        # Run CityDawg
        self.run()


    def run(self):

        # Get the genes we want to run on
        genes = self.get_genes()

        # For each gene
        for g in genes:
            self.process_gene(g)





    def get_definition_file(self, g):
        definition_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../definition/alleles/")
        filename = "%s_translation.json" % g
        definition_file = os.path.join(definition_dir, filename)
        return definition_file

    def get_genes(self):
        genes = ['CYP2C9', 'CYP2C19']
        #genes = ['CFTR', 'CYP2C9', 'CYP4F2', 'IFNL3', 'TPMT', 'VKORC1',
        #         'CYP2C19', 'CYP3A5',  'DPYD', 'SLCO1B1', 'UGT1A1']

        if self.gene == 'all':
            return genes
        # todo make this strict again.  Leaving out now for debugging purposes
        #if not self.gene in genes:
        #    print("Selected gene not available.  Please choose from list:")
        #    print(",".join(genes))
        #    exit(1)
        return [self.gene]

    def process_gene(self, g):

        if self.debug:
            print("Processing %s" % g)
            print("Preparing reference haplotypes")

        preparation_start_time = timer()

        # Get the definition file
        gene_definition = self.get_definition_file(g)
        gene = Gene.Gene(gene_definition, build=self.build, debug=self.debug)
        hap_matrix, stars = gene.haplotype_matrix()
        preparation_end_time = timer()

        if self.debug:
            print("Preparation finished")
            print(hap_matrix.shape)
            print("Execution time: %s" % timedelta(seconds = preparation_end_time - preparation_start_time))


        if self.debug:
            print("Extracting genotype matrices")

        extraction_start_time = timer()
        gp = GenotypeParser(self.vcf, gene, debug=self.debug)
        gt_matrices = gp.haplotype_matrices(batch_mode=self.batch_mode)
        extraction_end_time = timer()

        if self.debug:
            print("Genotype extraction finished")
#             print(gt_matrices[0].shape)
#             print(gt_matrices[1].shape)
            print("Execution time: %s" % timedelta(seconds=extraction_end_time - extraction_start_time))

#             print("Number of alterate alleles in matrix A: %s" % np.sum(gt_matrices[0]))
#             print("Number of alterate alleles in matrix B: %s" % np.sum(gt_matrices[1]))

        if self.debug:
            print("Calling diplotypes")

        diplotype_caller_start_time = timer()

        dipCal = DiplotypeCaller(gene, is_phased = self.phased)

        sample_ids = get_vcf_subject_ids(self.vcf)
        sample_calls = []
        for gt_mat in gt_matrices:
            for samp in range(gt_mat[0].shape[1]):
                cd_call = dipCal.call_diplotype([gt_mat[0][:, samp], gt_mat[1][:, samp]]) 
                sample_calls.append(cd_call)

            diplotype_caller_end_time = timer()

        if self.debug:
            print("Diplotype calling finished")
            print("Execution time: %s" % timedelta(seconds=diplotype_caller_end_time - diplotype_caller_start_time))

            for i in range(len(sample_calls)):
                print("%s: %s" % (sample_ids[i], sample_calls[i]))



"""
Parse the command line
"""
def parse_command_line():
    welcome_message()
    parser = argparse.ArgumentParser(
        description = 'CityDawg determines star allele haplotypes for samples in a VCF file and outputs predicted '
                      'pharmacogenetic phenotypes.')
    parser.add_argument("--vcf", help="Input VCF")
    parser.add_argument("-g", "--gene", default='all', help="Gene to run.  Select from [].  Run all by default.")
    parser.add_argument("--phased", action='store_true', default=False, help="Data is phased.  Will try to determine phasing status "
                                                              "from VCF by default.")
    parser.add_argument("--build", default='grch38', help="Select build genome reference.  By default CityDawg assumes "
                                                            "GRCh38.")
    parser.add_argument("-d", "--debug", action='store_true', default=False,
                                help="Output debugging messages.  May be very verbose.")
    parser.add_argument("-b", "--batch", action='store_true', default=False,
                        help="Fragment into batched sample runs. Suggested for runs with more than 10k samples.")
    options = parser.parse_args()
    return options


"""
Main
"""
if __name__ == "__main__":
    options = parse_command_line()
    CityDawg(vcf=options.vcf, gene=options.gene, phased=options.phased, build=options.build, debug=options.debug, batch_mode=options.batch)





