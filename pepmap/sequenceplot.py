# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/SequencePlot.ipynb (unless otherwise specified).

__all__ = ['ptm_shape_dict', 'get_plot_data', 'plot_single_peptide_traces', 'plot_peptide_traces']

# Cell
ptm_shape_dict = {'[Phospho (STY)]': 0,
                '[GlyGly (K)]':2,
                '[Carbamidomethyl (C)]':3,
                '[Oxidation (M)]':4,
                '[Acetyl (Protein N-term)]':5}

# Cell
import numpy as np
import pandas as pd
from pyteomics import fasta

def get_plot_data(protein,df,fasta):
    protein_sequence = fasta[protein].sequence
    df_prot = df[df.unique_protein_id==protein]

    if df_prot.shape[0] == 0:
        df_plot = None
    else:
        df_peps = [np.arange(row['start'], row['end']+1) for _, row in df_prot.iterrows()]
        df_peps  = pd.DataFrame.from_records(data=df_peps)
        df_peps['modified_sequence'] = df_prot['modified_sequence'].values
        df_peps = df_peps.melt(id_vars=['modified_sequence'])
        df_peps = df_peps[['modified_sequence','value']].dropna()
        df_peps = df_peps.rename(columns={"value": "seq_position"})
        df_peps['marker_symbol'] = 1
        df_peps['marker_size'] = 8
        df_peps['PTM'] = np.NaN
        df_peps['PTMtype'] = np.NaN
        df_peps['PTMshape'] = np.NaN
        unique_pep = df_peps.modified_sequence.unique()
        for uid in unique_pep:
            df_peps_uid = df_peps[df_peps.modified_sequence==uid]
            start_uid = np.min(df_peps_uid.seq_position)
            end_uid = np.max(df_peps_uid.seq_position)
            df_peps['marker_symbol'] = np.where(df_peps.seq_position == start_uid, 7, df_peps.marker_symbol)
            df_peps['marker_symbol'] = np.where(df_peps.seq_position == end_uid, 8, df_peps.marker_symbol)
            df_peps['marker_size'] = np.where(df_peps.seq_position == start_uid, 6, df_peps.marker_size)
            df_peps['marker_size'] = np.where(df_peps.seq_position == end_uid, 6, df_peps.marker_size)

            df_PTMs_uid = df_prot[df_prot.modified_sequence==uid]
            PTMsites = df_PTMs_uid.PTMsites.tolist()[0] + start_uid
            PTMtypes = df_PTMs_uid.PTMtypes.tolist()[0]

            for i in range(0,len(PTMsites)):
                df_peps['PTM'] = np.where(df_peps["seq_position"]==PTMsites[i], 1, df_peps.PTM)
                df_peps['PTMtype'] = np.where(df_peps["seq_position"]==PTMsites[i], PTMtypes[i], df_peps.PTMtype)

            df_seq = pd.DataFrame({'seq_position':np.arange(0,len(protein_sequence))})

            df_plot = pd.merge(df_seq, df_peps, how='left', on='seq_position')
            df_plot['height']=0
            df_plot['color']="grey"

            unique_mods = df_plot['PTMtype'].dropna().unique()
            if len(unique_mods) > 0:
                for mod in df_plot['PTMtype'].dropna().unique():
                    if mod != 'nan':
                        df_plot.loc[df_plot.PTMtype == mod, 'PTMshape'] = ptm_shape_dict[mod]

    return(df_plot)

# Cell
import plotly.graph_objects as go

def plot_single_peptide_traces(df_plot,protein,fasta):
    protein_sequence = fasta[protein].sequence

    ## Peptide backbone
    df_plot_pep = df_plot.dropna(subset=['modified_sequence'])
    plot1 = go.Scatter(x=df_plot_pep.seq_position,
                               y=df_plot.height,
                               xaxis='x1',
                               mode='markers',
                               marker_size=df_plot_pep.marker_size,
                               marker_symbol=df_plot_pep.marker_symbol,
                               marker_line_color=df_plot_pep.color,
                               marker_color=df_plot_pep.color,
                               marker_opacity=1,
                       hovertext=df_plot_pep.seq_position+1,
                                     hoverinfo='all',
                               #text=df_plot_pep.seq_position+1,
                               #hovertemplate='%{text}',
                       name='',
                       showlegend=False)

    ## PTM dots
    df_plot_ptm = df_plot.dropna(subset=['PTM'])
    #print(df_plot_ptm)
    plot2 = go.Scatter(x=df_plot_ptm.seq_position,
                               y=df_plot_ptm.height+0.3,
                               xaxis='x1',
                               mode='markers',
                               marker_size=8,
                               marker_symbol=df_plot_ptm.PTMshape,
                               marker_line_color=df_plot_ptm.color,
                               marker_color=df_plot_ptm.color,
                               marker_opacity=1,
                       hovertext=df_plot_ptm.PTMtype,
                                     hoverinfo='text',
                               #text=df_plot_ptm.PTMtype,
                               #hovertemplate='%{text}',
                       name='',
                       showlegend=False)

    layout = go.Layout(
            yaxis=dict(
                title = "",
                ticks = None,
                showticklabels=False,
                range=[-1, 2]
                ),
            xaxis=dict(
                title= 'protein sequence',
                tickmode = 'array',
                range=[-10, len(protein_sequence)+10],
                tickvals = np.arange(0,len(protein_sequence)),
                ticktext = list(protein_sequence),
                tickangle=0
            ),
        #showlegend=False,
        #height=400, width=1000,
        plot_bgcolor='rgba(0,0,0,0)',
        title=f"Sequence plot for {protein}:"
        )

    fig = go.Figure(data=[plot1,plot2], layout=layout)

    for i in range(0, df_plot_ptm.shape[0]):
            fig.add_shape(
                    dict(
                        type="line",
                        x0=df_plot_ptm.seq_position.values[i],
                        y0=df_plot_ptm.height.values[i],
                        x1=df_plot_ptm.seq_position.values[i],
                        y1=df_plot_ptm.height.values[i]+0.3,
                        line=dict(
                            color=df_plot_ptm.color.values[i],
                            width=1
                        )
                    )
            )

    return fig

# Cell

import plotly.graph_objects as go

def plot_peptide_traces(df,name,protein,fasta,uniprot,selected_features):

    colors = ['#E24A33', '#348ABD', '#988ED5', '#777777', '#FBC15E', '#8EBA42', '#FFB5B8']

    uniprot_annotation_p = uniprot[uniprot.protein_id==protein]
    uniprot_annotation_p_f = uniprot_annotation_p[uniprot_annotation_p.feature.isin(selected_features)]

    if isinstance(df, pd.DataFrame):
        df_plot = get_plot_data(protein=protein,
                              df = df,
                              fasta = fasta)

        df_plot.color = colors[0]

        observed_mods = list(set(df_plot.PTMtype))
        ptm_shape_dict_sub = {key: ptm_shape_dict[key] for key in observed_mods if key in ptm_shape_dict}

        fig = plot_single_peptide_traces(df_plot,protein=protein,fasta = fasta)
        fig.update_layout(yaxis=dict(showticklabels=True,
                                     tickmode = 'array',
                                     tickvals = [0],
                                     ticktext = [name]))

        y_max = 1

    elif isinstance(df, list):

        df_plot = [get_plot_data(protein=protein,
                               df = d,
                               fasta = fasta) for d in df]

        # Subset data and annotations for the samples where the selected protein was detected
        valid_idx = []
        for i in range(len(df_plot)):
            if df_plot[i] is not None:
                valid_idx.append(i)
        df_plot = [df_plot[i] for i in valid_idx]
        name = [name[i] for i in valid_idx]
        colors = [colors[i] for i in valid_idx]
        #observed_mods = set([df_plot[i].PTMtype for i in valid_idx])
        observed_mods = []
        for i in range(len(df_plot)):
            observed_mods.extend(list(set(df_plot[i].PTMtype)))
        observed_mods = list(set(observed_mods))
        ptm_shape_dict_sub = {key: ptm_shape_dict[key] for key in observed_mods if key in ptm_shape_dict}

        for i in range(len(df_plot)):
            df_plot[i].color = colors[i]
            df_plot[i].height = 1+i

        plot_list = [plot_single_peptide_traces(df,protein=protein,fasta = fasta) for df in df_plot]
        new_data = [p.data for p in plot_list]
        new_data = sum(new_data, ())
        new_layout = plot_list[0].layout
        shapes = [p.layout.shapes for p in plot_list]
        shapes = sum(shapes, ())
        new_layout.shapes = new_layout.shapes + tuple(shapes)
        fig = go.Figure(data=new_data, layout=new_layout)
        fig.update_layout(yaxis=dict(range=[0,len(df_plot)+1],
                                     showticklabels=True,
                                     tickmode = 'array',
                                     tickvals = np.arange(0, len(df_plot))+1,
                                     ticktext = np.array(name)))

        y_max = len(df_plot)+1


    ptm_shape_dict_sub = dict(sorted(ptm_shape_dict_sub.items()))
    for i in range(len(ptm_shape_dict_sub)):
        fig.add_trace(go.Scatter(y=[None],
                                 mode='markers',
                                 marker=dict(symbol=list(ptm_shape_dict_sub.values())[i],
                                             color='black'),
                                 name=list(ptm_shape_dict_sub.keys())[i],
                                 showlegend=True))

    unique_features = list(set(uniprot_annotation_p_f.feature))
    if len(unique_features) > 0:
        for j in range(0,len(unique_features)):
            domain = unique_features[j]
            domain_info_sub = uniprot_annotation_p_f[uniprot_annotation_p_f.feature==domain].reset_index(drop=True)
            for i in range(0, domain_info_sub.shape[0]):
                start=int(domain_info_sub.start[i])
                end=int(domain_info_sub.end[i])
                if start==end:
                    end=end+1

                #fig.add_shape(
                #    dict(
                #        type="line",
                #        x0=start-1,
                #        y0=y_max+j+(i/5),
                #        x1=end-1,
                #        y1=y_max+j+(i/5),
                #        line=dict(
                #            color="pink",
                #            width=6
                #        )
                #    )
                #)
                fig.add_trace(go.Bar(x=list(range(start-1,end-1)),
                         y=list(np.repeat(0.2,end-start)),
                         base=list(np.repeat(y_max+j,end-start)-0.1),
                         marker_color='grey',
                                     opacity=0.8,
                                     showlegend=False,
                                     name='',
                                   hovertext=domain_info_sub.note[i],
                                     hoverinfo='text'
                                    ))
        fig.update_layout(barmode='stack', bargap=0, hovermode='x unified',hoverdistance=1)


    if isinstance(df, pd.DataFrame):
        fig.update_yaxes(showticklabels=True,
                         tickvals= np.arange(0, 1+len(unique_features)),
                         ticktext=np.append(np.array(name),np.array(unique_features)),
                         automargin=True,
                         range=[0, 1+len(unique_features)+1])
    elif isinstance(df, list):
        fig.update_yaxes(showticklabels=True,
                         tickvals= 1 + np.arange(0, len(df_plot)+len(unique_features)),
                         ticktext=np.append(np.array(name),np.array(unique_features)),
                         automargin=True,
                         range=[0, len(df_plot)+len(unique_features)+1])

    return fig