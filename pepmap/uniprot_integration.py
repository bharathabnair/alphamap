# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/Uniprot_integration.ipynb (unless otherwise specified).

__all__ = ['extract_note', 'extract_note_end', 'resolve_unclear_position', 'extract_positions', 'preprocess_uniprot']

# Cell
import re

import pandas as pd
import numpy as np

# Cell
def extract_note(string, splitted=False):
    """
    Function to extract information about note of the protein from Uniprot using regular expression
    """
    if not splitted:
        regex = r"\/note=\"(?P<note>.+?)\""
    else:
        regex = r"\/note=\"(?P<note>.*)"
    result = re.findall(regex, string)
    return result

def extract_note_end(string, has_mark=True):
    if has_mark:
        regex = r"FT\s+(?P<note>.*)\""
    else:
        regex = r"FT\s+(?P<note>.*)"
    result = re.findall(regex, string)
    return result

# Cell
def resolve_unclear_position(value):
    """
    Replace unclear position of the start/end of the modification defined as '?' with -1 and if it's defined as '?N'
    or ">N" - by removing the '?'/'>'/'<' signs
    """
    # if it's "1..?" or "?..345" for start or end -> remove -1 that we can filter later
    # if it's "31..?327" or "?31..327" -> remove the question mark
    # if it's "<1..106" or "22..>115" -> remove the "<" or ">" signs
    if value == '?':
        return -1
    value = value.replace('?', '').replace('>', '').replace('<', '')
    return int(value)

def extract_positions(posit_string):
    """
    Extract isoform_id(str) and start/end positions(int, int/float) of any feature key from the string
    """
    isoform = ''
    start = end = np.nan
    if '..' in posit_string:
        start, end = posit_string.split('..')
    if ':' in posit_string:
        if isinstance(start, str):
            isoform, start = start.split(':')
        else:
            isoform, start = posit_string.split(':')
    # in the case when we have only one numeric value as a posit_string
    if isinstance(start, float):
        start = posit_string
    # change the type of start and end into int/float(np.nan)
    if isinstance(start, str):
        start = resolve_unclear_position(start)
    if isinstance(end, str):
        end = resolve_unclear_position(end)
    return isoform, start, end

# Cell
def preprocess_uniprot(path_to_file):
    """
    A complex complete function to preprocess Uniprot data from specifying the path to a flat text file
    to the returning a dataframe containing information about:
        - protein_id(str)
        - feature(category)
        - isoform_id(str)
        - start(int)
        - end(int)
        - note information(str)
    """
    all_data = []
    with open(path_to_file) as f:

        is_splitted = False
        new_instance = False
        combined_note = []
        line_type = ''

        for line in f:

            if line.startswith(('AC', 'FT')):
                if is_splitted:
                    # in case when the note information is splitted into several lines
                    if line.rstrip().endswith('"'):
                        # if it's the final part of the note
                        combined_note.extend(extract_note_end(line))
                        all_data.append([protein_id, feature, isoform, start, end, " ".join(combined_note)])
                        is_splitted = False
                        new_instance = False
                    else:
                        # if it's the middle part of the note
                        combined_note.extend(extract_note_end(line, has_mark=False))
                elif line.startswith('AC'):
                    # contains the protein_id information
                    if line_type != 'AC':
                        # to prevent a situation when the protein has several AC lines with different names
                        # in this case we are taking the first name in the first line
                        protein_id = line.split()[1].replace(';', '')
                    line_type = 'AC'
                elif line.startswith('FT'):
                    line_type = 'FT'
                    # contains all modifications/preprocessing events/etc., their positions, notes
                    data = line.split()
                    if data[1].isupper() and not data[1].startswith('ECO'):
                            feature = data[1]
                            isoform, start, end = extract_positions(data[2])
                            new_instance = True
                    else:
                        if data[1].startswith('/note'):
                            note = extract_note(line)
                            if note:
                                # if note was created > it contains just one line and can be already added to the data
                                all_data.append([protein_id, feature, isoform, start, end, note[0]])
                                new_instance = False
                            else:
                                # if note is empty > it's splitted into several lines and we create combined_note
                                combined_note = extract_note(line, splitted=True)
                                is_splitted = True
                        else:
                            if new_instance:
                                # in case when we don't have any note but need to add other information about instance
                                all_data.append([protein_id, feature, isoform, start, end, ''])
                                new_instance = False

    # create a dataframe for preprocessed data
    uniprot_df = pd.DataFrame(all_data, columns=['protein_id', 'feature', 'isoform_id', 'start', 'end', 'note'])
    # change the dtypes of the columns
    uniprot_df.feature = uniprot_df.feature.astype('category')
    uniprot_df.end = uniprot_df.end.astype('Int64')
    # to filter the instances that don't have a defined start/end position(start=-1 or end=-1)
    uniprot_df = uniprot_df[(uniprot_df.start != -1) & (uniprot_df.end != -1)]

    return uniprot_df