import sqlite3
from utils import *
from func_timeout import func_timeout, FunctionTimedOut
from llm_request import *
from const import *
class Corrector(object):
    def __init__(self, database_path: str):
        super().__init__()
        # root directory of all databases
        self.database_path = database_path 

    def execute_model(self, db_id, sql, topn):
        db_path = f"{self.database_path}/{db_id}/{db_id}.sqlite"
        conn = sqlite3.connect(db_path)
        conn.text_factory = lambda b: b.decode(errors="ignore")
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
            result = cursor.fetchall()
            return {
                "sql": sql,
                "data": result[:topn],
                "sqlite_error": "",
                "exception_class": ""
            }
        except sqlite3.Error as er:
            return {
                "sql": str(sql),
                "sqlite_error": str(' '.join(er.args)),
                "exception_class": str(er.__class__)
            }
        except Exception as e:
            return {
                "sql": str(sql),
                "sqlite_error": str(e.args),
                "exception_class": str(type(e).__name__)
            }


    def correction(self, db_id: str, sql: str, query: str, evidence: str, schema_info: str, origin_schema_info, fk_info: str,idx=0, meta_time_out=30.0, topn=5, MAX_NUMS=3):
        re_sql = "[No changed]"+sql
        prompt = ""
        final_i = 0
        for i in range(MAX_NUMS):
            error_info = self.execute_model(db_id, sql, topn)
            if i+1 >= MAX_NUMS*0.8:
                schema_info = origin_schema_info

            if self._is_need_correct(error_info):
                sql_arg = add_prefix(error_info.get('sql'))
                sqlite_error = error_info.get('sqlite_error')
                exception_class = error_info.get('exception_class')
                prompt = refiner_template.format(query=query, evidence=evidence, desc_str=schema_info, \
                                            fk_str=fk_info, sql=sql_arg, sqlite_error=sqlite_error, \
                                                exception_class=exception_class)
                re_sql = request_llm(prompt)
                if re_sql != '':
                    sql = select_final_sql(re_sql, "```")
                    sql = clean_result(sql)
                else:
                    sql = re_sql
                final_i += 1
            else:
                break
        re_sql = "【Correction rounds】" + str(final_i) + "\n" + re_sql
        return prompt, re_sql, sql

    @staticmethod
    def _is_need_correct(exec_result: dict):
        data = exec_result.get('data', None)
        if data is not None:
            if len(data) == 0:
                exec_result['sqlite_error'] = 'no data selected'
                return True
            return False
        else:
            return True
















if __name__ == '__main__':
    # NOTICE:
    db_root_path = './data/dev/dev_databases'
    db_id = 'california_schools'
    sql = "SELECT CAST(COUNT(CASE WHEN FundingType = 'Local' THEN 1 ELSE 0 END) AS REAL / CAST(COUNT(CASE WHEN County = 'Santa Clara' AND Charter IS NOT NULL AND Charter != 0 THEN 1 ELSE 0 END) AS REAL) * 100 AS percentage FROM schools WHERE County = 'Santa Clara'"
    prefix_prompt = ''
    idx = 99
    query = 'What is the ratio in percentage of Santa Clara County schools that are locally funded compared to all other types of charter school funding?'
    pre_knowledge_schema = """
# Table: frpm\n[\n  (Charter Funding Type: field type is TEXT, Value examples: [None, 'Directly funded', 'Locally funded', 'Not in CS funding model']),\n  (District Type: field type is TEXT, Value examples: ['Unified School District', 'Elementary School District', 'High School District', 'County Office of Education (COE)', 'State Board of Education']),\n  (Charter School Number: field type is TEXT, Value examples: [None, '00D2', '0756', '00D4', '00D1', '1700']),\n  (District Code: field type is INTEGER),\n  (Charter School (Y/N): field type is INTEGER, 0: N; 1: Y, Value examples: [None, 0, 1]),\n  (Percent (%) Eligible FRPM (K-12): field type is REAL),\n  (County Code: field type is TEXT, Value examples: ['19', '37', '30', '36', '33']),\n  (District Name: field type is TEXT),\n  (Percent (%) Eligible Free (K-12): field type is REAL),\n  (School Code: field type is TEXT, Value examples: ['0000000', '9010745', '6121081', '6121073', '6121016']),\n  (School Type: field type is TEXT, Value examples: [None, 'Elementary Schools (Public)', 'High Schools (Public)', 'Intermediate/Middle Schools (Public)', 'Continuation High Schools', 'Alternative Schools of Choice']),\n  (County Name: County Code, field type is TEXT, Value examples: ['Los Angeles', 'San Diego', 'Orange', 'San Bernardino', 'Riverside']),\n  (FRPM Count (K-12): Free or Reduced Price Meal Count (K-12), field type is REAL, commonsense evidence:  eligible FRPM rate = FRPM / Enrollment),\n  (Percent (%) Eligible FRPM (Ages 5-17): field type is REAL),\n  (FRPM Count (Ages 5-17): field type is REAL),\n  (Enrollment (Ages 5-17): field type is REAL),\n  (Enrollment (K-12): field type is REAL, commonsense evidence:  K-12: 1st grade - 12nd grade),\n  (Free Meal Count (K-12): field type is REAL, commonsense evidence:  eligible free rate = Free Meal Count / Enrollment),\n  (Percent (%) Eligible Free (Ages 5-17): field type is REAL),\n  (Educational Option Type: field type is TEXT, Value examples: [None, 'Traditional', 'Continuation School', 'Alternative School of Choice', 'Community Day School', 'Special Education School']),\n  (CDSCode: field type is TEXT, primary key, Value examples: ['01100170109835', '01100170112607', '01100170118489', '01100170123968', '01100170124172']),\n  (High Grade: field type is TEXT, Value examples: ['12', '5', '8', '6', '3']),\n  (School Name: field type is TEXT),\n  (Free Meal Count (Ages 5-17): field type is REAL, commonsense evidence:  eligible free rate = Free Meal Count / Enrollment),\n  (IRC: field type is INTEGER, Not useful, Value examples: [None, 0, 1]),\n  (NSLP Provision Status: field type is TEXT, Value examples: [None, 'Provision 2', 'Breakfast Provision 2', 'CEP', 'Multiple Provision Types', 'Provision 1']),\n]\n
# Table: schools\n[\n  (FundingType: Indicates the charter school funding type, field type is TEXT, Values are as follows:  \u00b7\u00a0\u00a0\u00a0\u00a0\u00a0\u00a0 Not in CS (California School) funding model  \u00b7\u00a0\u00a0\u00a0\u00a0\u00a0\u00a0 Locally funded  \u00b7\u00a0\u00a0\u00a0\u00a0\u00a0\u00a0 Directly funded, Value examples: [None, 'Directly funded', 'Locally funded', 'Not in CS funding model']),\n  (DOC: District Ownership Code, field type is TEXT, The District Ownership Code (DOC) is the numeric code used to identify the category of the Administrative Authority.        00 - County Office of Education        02 \u2013 State Board of Education        03 \u2013 Statewide Benefit Charter        31 \u2013 State Special Schools        34 \u2013 Non-school Location*        52 \u2013 Elementary School District        54 \u2013 Unified School District        56 \u2013 High School District        98 \u2013 Regional Occupational Center/Program (ROC/P) commonsense evidence: *Only the California Education Authority has been included in the non-school location category, Value examples: ['54', '52', '00', '56', '98']),\n  (CharterNum: The charter school number,, field type is TEXT, 4-digit number assigned to a charter school, Value examples: [None, '00D2', '0756', '00D4', '00D1', '1826']),\n  (NCESDist: National Center for Educational Statistics school district identification number. This field represents the 7-digit National Center for Educational Statistics (NCES) school district identification number. The first 2 digits identify the state and the last 5 digits identify the school district. Combined, they make a unique 7-digit ID for each school district, field type is TEXT, Value examples: [None, '0622710', '0634320', '0628050', '0634410', '0614550']),\n  (SOC: School Ownership Code. The School Ownership Code is a numeric code used to identify the type of school, field type is TEXT, 08 - Preschool              09 \u2013 Special Education Schools (Public)       11 \u2013 Youth Authority Facilities (CEA)        13 \u2013 Opportunity Schools        14 \u2013 Juvenile Court Schools        15 \u2013 Other County or District Programs        31 \u2013 State Special Schools        60 \u2013 Elementary School (Public)        61 \u2013 Elementary School in 1 School District (Public)        62 \u2013 Intermediate/Middle Schools (Public)        63 \u2013 Alternative Schools of Choice        64 \u2013 Junior High Schools (Public)        65 \u2013 K-12 Schools (Public)        66 \u2013 High Schools (Public)        67 \u2013 High Schools in 1 School District (Public)        68 \u2013 Continuation High Schools        69 \u2013 District Community Day Schools        70 \u2013 Adult Education Centers        98 \u2013 Regional Occupational Center/Program (ROC/P), Value examples: [None, '60', '66', '62', '68', '09']),\n  (District: field type is TEXT),\n  (GSoffered: grade span offered. The grade span offered is the lowest grade and the highest grade offered or supported by the school, district, or administrative authority. This field might differ from the grade span served as reported in the most recent certified California Longitudinal Pupil Achievement (CALPADS) Fall 1 data collection, field type is TEXT, For example XYZ School might display the following data:  GSoffered = P\u2013Adult  GSserved = K\u201312, Value examples: [None, 'K-5', '9-12', 'K-6', 'K-8', '6-8']),\n  (NCESSchool: National Center for Educational Statistics school identification number. This field represents the 5-digit NCES school identification number. The NCESSchool combined with the NCESDist form a unique 12-digit ID for each school, field type is TEXT, Value examples: [None, '12271', '13785', '13747', '12909', '12311']),\n  (Charter: This field identifies a charter school, field type is INTEGER, The field is coded as follows:  \u00b7\u00a0\u00a0\u00a0\u00a0\u00a0\u00a0 1 = The school is a charter  \u00b7\u00a0\u00a0\u00a0\u00a0\u00a0\u00a0 0 = The school is not a charter, Value examples: [None, 0, 1]),\n  (State: field type is TEXT, Value examples: [None, 'CA']),\n  (GSserved: grade span served. It is the lowest grade and the highest grade of student enrollment as reported in the most recent certified CALPADS Fall 1 data collection. Only K\u201312 enrollment is reported through CALPADS. This field may differ from the grade span offered, field type is TEXT, commonsense evidence:  1.\u00a0\u00a0\u00a0\u00a0 Only K\u201312 enrollment is reported through CALPADS  2.\u00a0\u00a0\u00a0\u00a0 Note: Special programs at independent study, alternative education, and special education schools will often exceed the typical grade span for schools of that type, Value examples: [None, 'K-5', 'K-6', '9-12', 'K-8', '6-8']),\n  (DOCType: The District Ownership Code Type. The District Ownership Code Type is the text description of the DOC category, field type is TEXT, (See text values in DOC field description above), Value examples: ['Unified School District', 'Elementary School District', 'County Office of Education (COE)', 'High School District', 'Regional Occupation Center/Program (ROC/P)']),\n  (County: County name, field type is TEXT, Value examples: ['Los Angeles', 'San Diego', 'Orange', 'San Bernardino', 'Santa Clara']),\n  (SOCType: School Ownership Code Type. The School Ownership Code Type is the text description of the type of school, field type is TEXT, The School Ownership Code Type is the text description of the type of school, Value examples: [None, 'Elementary Schools (Public)', 'High Schools (Public)', 'Intermediate/Middle Schools (Public)', 'Continuation High Schools', 'Special Education Schools (Public)']),\n  (Ext: extension. The phone number extension of the school, district, or administrative authority, field type is TEXT, The phone number extension of the school, district, or administrative authority, Value examples: [None, '200', '201', '111', '352', '221']),\n  (CDSCode: field type is TEXT, primary key, Value examples: ['01100170000000', '01100170109835', '01100170112607', '01100170118489', '01100170123968']),\n  (EdOpsCode: Education Option Code. The Education Option Code is a short text description of the type of education offered, field type is TEXT, ALTSOC \u2013 Alternative School of Choice       COMM \u2013 County Community School        COMMDAY \u2013 Community Day School        CON \u2013 Continuation School        JUV \u2013 Juvenile Court School        OPP \u2013 Opportunity School        YTH \u2013 Youth Authority School        SSS \u2013 State Special School        SPEC \u2013 Special Education School        TRAD \u2013 Traditional        ROP \u2013 Regional Occupational Program        HOMHOS \u2013 Home and Hospital        SPECON \u2013 District Consortia Special Education School, Value examples: [None, 'TRAD', 'CON', 'COMMDAY', 'ALTSOC', 'SPEC']),\n  (EILCode: Educational Instruction Level Code. The Educational Instruction Level Code is a short text description of the institution's type relative to the grade range served, field type is TEXT, A \u2013 Adult        ELEM \u2013 Elementary        ELEMHIGH \u2013 Elementary-High Combination        HS \u2013 High School        INTMIDJR \u2013 Intermediate/Middle/Junior High        PS \u2013 Preschool        UG \u2013 Ungraded, Value examples: [None, 'ELEM', 'HS', 'UG', 'INTMIDJR', 'ELEMHIGH']),\n  (MailCity: mailing city. , field type is TEXT, The city associated with the mailing address of the school, district, or administrative authority. Note: Many entities have not provided a mailing address city. For your convenience we have filled the unpopulated MailCity cells with City data, Value examples: [None, 'Los Angeles', 'San Diego', 'San Jose', 'Sacramento', 'Oakland']),\n  (MailState: mailing state. , field type is TEXT, The state within the mailing address. For your convenience we have filled the unpopulated MailState cells with State data, Value examples: [None, 'CA']),\n  (School: field type is TEXT),\n  (Magnet: This field identifies whether a school is a magnet school and/or provides a magnet program, field type is INTEGER, The field is coded as follows:  \u00b7\u00a0\u00a0\u00a0\u00a0\u00a0\u00a0 Y = Magnet - The school is a magnet school and/or offers a magnet program.  \u00b7\u00a0\u00a0\u00a0\u00a0\u00a0\u00a0 N = Not Magnet - The school is not a magnet school and/or does not offer a magnet program.  commonsense evidence:  Note: Preschools and adult education centers do not contain a magnet school indicator, Value examples: [None, 0, 1]),\n  (MailZip: mailing zip. , field type is TEXT, The zip code associated with the mailing address of the school, district, or administrative authority. Note: Many entities have not provided a mailing address zip code. For your convenience we have filled the unpopulated MailZip cells with Zip data, Value examples: [None, '94606', '91710-4130', '92626-4300', '90266', '95336-0032']),\n  (MailStrAbr: mailing street address. , field type is TEXT, the abbreviated mailing street address of the school, district, or administrative authority.Note: Many active entities have not provided a mailing street address. For your convenience we have filled the unpopulated MailStrAbr cells with StreetAbr data),\n  (City: field type is TEXT, Value examples: [None, 'Los Angeles', 'San Diego', 'San Jose', 'Sacramento', 'Fresno']),\n]\n
    """
    knowledge_fk = "frpm.CDSCode=schools.CDSCode\nsatscores.cds=schools.CDSCode"
    
    corrector = Corrector(db_root_path)
    db_id = 'toxicology'
    sql = "SELECT T.bond_type FROM ( SELECT T1.bond_type, COUNT(T2.molecule_id) FROM bond AS T1 INNER JOIN molecule AS T2 ON T1.molecule_id = T2.molecule_id WHERE T2.molecule_id = 'TR018' GROUP BY T1.bond_type ORDER BY COUNT(T2.molecule_id) DESC LIMIT 1 ) t"
    res = corrector.execute_model(db_id, sql, 5)
    print(res)
    
