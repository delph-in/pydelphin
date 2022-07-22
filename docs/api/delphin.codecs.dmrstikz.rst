
delphin.codecs.dmrstikz
=======================

.. automodule:: delphin.codecs.dmrstikz

This requires LaTeX and the `tikz-dependency
<https://ctan.org/pkg/tikz-dependency>`_ package.

Example:

* *The new chef whose soup accidentally spilled quit and left.*

  ::

     \documentclass{standalone}

     \usepackage{tikz-dependency}
     \usepackage{relsize}

     %%%
     %%% style for dmrs graph
     %%%
     \depstyle{dmrs}{edge unit distance=1.5ex,
       label style={above, scale=.9, opacity=0, text opacity=1},
       baseline={([yshift=-0.7\baselineskip]current bounding box.north)}}
     %%% set text opacity=0 to hide text, opacity = 0 to hide box
     \depstyle{root}{edge unit distance=3ex, label style={opacity=1}}
     \depstyle{arg}{edge above}
     \depstyle{rstr}{edge below, dotted, label style={text opacity=1}}
     \depstyle{eq}{edge below, label style={text opacity=1}}
     \depstyle{icons}{edge below, dashed}
     \providecommand{\named}{}
     \renewcommand{\named}{named}

     %%% styles for predicates and roles (from mrs.sty)
     \providecommand{\spred}{}
     \renewcommand{\spred}[1]{\mbox{\textsf{#1}}}
     \providecommand{\srl}{}
     \renewcommand{\srl}[1]{\mbox{\textsf{\smaller #1}}}
     %%%

     \begin{document}
     \begin{dependency}[dmrs]
       \begin{deptext}[column sep=10pt]
         \spred{\_the\_q} \&     % node 1
         \spred{\_new\_a\_1} \&     % node 2
         \spred{\_chef\_n\_1} \&     % node 3
         \spred{def\_explicit\_q} \&     % node 4
         \spred{poss} \&     % node 5
         \spred{\_soup\_n\_1} \&     % node 6
         \spred{\_accidental\_a\_1} \&     % node 7
         \spred{\_spill\_v\_1} \&     % node 8
         \spred{\_quit\_v\_1} \&     % node 9
         \spred{\_and\_c} \&     % node 10
         \spred{\_leave\_v\_1} \\     % node 11
       \end{deptext}
       \deproot[root]{9}{\srl{TOP}}
       \depedge[rstr]{1}{3}{\srl{RSTR/H}}
       \depedge[eq]{2}{3}{\srl{ARG1/EQ}}
       \depedge[rstr]{4}{6}{\srl{RSTR/H}}
       \depedge[eq]{5}{6}{\srl{ARG1/EQ}}
       \depedge[arg]{5}{3}{\srl{ARG2/NEQ}}
       \depedge[eq]{7}{8}{\srl{ARG1/EQ}}
       \depedge[arg]{8}{6}{\srl{ARG1/NEQ}}
       \depedge[arg]{9}{3}{\srl{ARG1/NEQ}}
       \depedge[eq]{10}{9}{\srl{ARG1/EQ}}
       \depedge[eq]{10}{11}{\srl{ARG2/EQ}}
       \depedge[arg]{11}{3}{\srl{ARG1/NEQ}}
       \depedge[eq]{8}{3}{\srl{MOD/EQ}}
       \depedge[eq]{11}{9}{\srl{MOD/EQ}}
       %  \depedge[icons]{f}{t}{FOCUS}
     \end{dependency}

     \end{document}

  This renders as the following:

  .. image:: ../_static/dmrs-tikz-pdf.png


Serialization Functions
-----------------------

.. function:: dump(ms, destination, properties=True, lnk=True, indent=False, encoding='utf-8')

   See the :func:`dump` codec API documentation.

.. function:: dumps(ms, properties=True, lnk=True, indent=False)

   See the :func:`dumps` codec API documentation.

.. function:: encode(m, properties=True, lnk=True, indent=False)

   See the :func:`encode` codec API documentation.
