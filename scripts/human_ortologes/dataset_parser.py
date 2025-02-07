from db import dao
import os
import csv
import requests
from entities.entities import Gene, Source, GeneToSource, CalorieRestrictionExperiment
import time
from mysql.connector.errors import DataError
import traceback


def parser():
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    calory_restrictions = open(os.path.join(cur_dir, 'Calory_restriction_datasets-2 - Sheet1.csv'))
    reader = csv.DictReader(calory_restrictions)
    source = Source(name='calorie_restriction')
    result = dao.SourceDAO().get_source(source=source)
    calorie_dao = dao.CalorieExperimentDAO()
    if result:
        source_id = result['id']
    else:
        result = dao.SourceDAO().add_source(source=source)
        source_id = result['id']
    for row in reader:
        gene_db = dao.GeneDAO().get_by_symbol(gene=row['symbol'])
        try:
            gene_source = dao.GeneDAO().get_source_gene(gene_db['symbol'])
            if gene_source['name'] == 'calorie_restriction':
                continue
        except TypeError:
            pass
        if gene_db:
            gene_id = gene_db['id']
            gene_symbol = gene_db['symbol']
        if not gene_db:
            gene = requests.get('https://mygene.info/v3/query'
                                '?fields=symbol%2Cname%2Centrezgene%2Calias%2Csummary'
                                '&species=human&q={}'.format(row['symbol']))
            if 'hits' not in gene.json():
                continue
            if len(gene.json()['hits']) > 0:
                gene_answer = gene.json()['hits'][0]
                gene = Gene(
                    isHidden=1,
                    symbol=gene_answer['symbol'],
                    name=gene_answer['name'],
                    created_at=time.time(),
                    updated_at=time.time(),
                )
                if 'alias' in gene_answer:
                    if type(gene_answer['alias']) == list:
                        gene.aliases = ','.join(gene_answer['alias'])
                    else:
                        gene.aliases = gene_answer['alias']
                if 'summary' in gene_answer:
                    gene.ncbi_summary_en = gene_answer['summary']
                if 'entrezgene' in gene_answer:
                    gene.ncbi_id = gene_answer['entrezgene']
                gene_symbol = gene.symbol
                gene_id = dao.GeneDAO().add(gene=gene)['id']
            else:
                continue
        gene_to_source = GeneToSource(
            gene_id=gene_id,
            source_id=source_id,
        )
        dao.SourceDAO().add_relation(gene_to_source=gene_to_source)
        if row['measurementMethod'] == "chromatography, mass_spectrometry" \
                or row['measurementMethod'] == "mass_spectrometry":
            measurement_method_str = row['measurementMethod']
        else:
            measurement_method_str = row['measurementMethod'].lower().replace('_', ' ')
        measurement_method_id = calorie_dao.get_measurement_method(name=measurement_method_str)['id']
        if row['organism'] == "mouse":
            organism = "mice"
            strain_id = calorie_dao.get_organism_line(row['line'])['id']
        elif row["organism"] == "monkey":
            organism = "rhesus monkeys"
            strain_id = None
        else:
            organism = row['organism']
            try:
                strain_id = calorie_dao.get_organism_line(row['line'])['id']
            except TypeError:
                print(row['line'])
                continue
        if row['sex'] == "both":
            sex = 'mixed'
        else:
            sex = row['sex']
        try:
            tissue_str = row['tissue'].lower().replace('_', ' ')
            tissue_id = calorie_dao.get_sample(name=tissue_str)['id'],
        except TypeError:
            tissue_str = row['tissue'].lower().replace('_', ' ')
            result = calorie_dao.add_sample(name=tissue_str)
            tissue_id = result['id']
        if len(row['isoform']) > 0:
            try:
                isoform_id = calorie_dao.get_isoform(name=row['isoform'])['id'],
            except TypeError:
                result = calorie_dao.add_isoform(name=row['isoform'])
                isoform_id = result['id']
        else:
            isoform_id = None
        calory_restriction_object = CalorieRestrictionExperiment(
            gene_id=gene_id,
            symbol=gene_symbol,
            p_val=row['pValue'],
            result=row['crResult'],
            measurement_method_id=measurement_method_id,
            measurement_type_id=calorie_dao.get_measurement_type(name=row['measurementType'].lower().replace('_', ' '))['id'],
            restriction_percent=row['restrictionPercent'],
            restriction_time=row['restrictionTime'].split('_')[0],
            restriction_time_unit_id=calorie_dao.get_treatment_time(row['restrictionTime'].split('_')[1])[
                'id'],
            age=row['age'].split('_')[0],
            tissue_id=calorie_dao.get_sample(name=row['tissue'])['id'],
            age_time_unit_id=calorie_dao.get_treatment_time(row['age'].split('_')[1])['id'],
            model_organism_id=calorie_dao.get_model_organism(organism)['id'],
            strain_id=strain_id,
            organism_sex_id=calorie_dao.get_organism_sex(sex)['id'],
            experiment_number=row['experimentNumber'],
            expression_change_log_fc=row['lexpressionChangeLogFc'],
            expression_change_percent=row['expressionChangePercent'],
            doi=row['doi'],
            isoform=isoform_id,
        )
        calorie_dao.add_experiment(experiment=calory_restriction_object)


parser()
