from sympy import symbols, Eq, solve, S, latex, conjugate, Rational
from sympy.core.numbers import Rational, Zero, One
from sympy.printing.mathml import print_mathml
from graphviz import Digraph

"""module de création d'un arbre de probabilité à 2 événements

il faut entrer suffisamment de probabilités,
éventuellement préciser si les événements sont indépendants.
L'objet construit l'arbre de la situation et le résout en recherchant 
toutes les probabilités manquantes.

On peut générer:
* un arbre d'énoncé vide avec des pointillés à compléter
* un arbre d'énoncé avec les données remplies et des pointillés ailleurs
* un arbre complet avec ou sans les probabilités des intersections

On peut choisir le format de présentation des probabilités:
decimal, pourcentage, fraction
"""

a,ca,b,cb,ab,cab,acb,cacb,b_a = symbols("a ca b cb ab cab acb cacb b_a")
cb_a,b_ca,cb_ca,a_b,ca_b = symbols("cb_a b_ca cb_ca a_b ca_b")
a_cb,ca_cb = symbols("a_cb ca_cb")

class arbre_proba():
    """classe de création d'un arbre de probabilité à 2 événements

    :param nbformat: in ['fraction', 'pourcentage', 'decimal']
    :param indep: booléen, indique si les événements sont indépendants
    :param mode: in ['full', 'partial'] full: indique si on doit afficher 
        toutes les probas d'intersection 
        (éventuellement avec des … de recherche)
        partial: on n'affiche que les intersections connues, et rien ailleurs
    :param intersection: indique si on remplit la probabilité de
        l'intersection en bout de branche quand elle est connue
    :type intersection: bool
    """
    
    def __init__(self, **kwargs):
        # gestion du format d'affichage des probabilités
        # self.nbformat in ['fraction','pourcentage', 'decimal']
        if "nbformat" in kwargs:
            self.nbformat = kwargs["nbformat"]
        else:
            self.nbformat = "pourcentage"
        # calcul de la précision
        self.precision = max([len(str(float(v)).partition(".")[2])
                              for v in kwargs.values()
                              if type(v) in [float, Rational, One, Zero]])
        
        s = "a ca b cb ab cab acb cacb b_a cb_a b_ca cb_ca a_b ca_b a_cb ca_cb".split()
        global a,ca,b,cb,ab,cab,acb,cacb,b_a,cb_a,b_ca,cb_ca,a_b,ca_b,a_cb,ca_cb
        Symb = [a,ca,b,cb,ab,cab,acb,cacb,b_a,cb_a,b_ca,cb_ca,a_b,ca_b,a_cb,
                ca_cb]
        # remplissage des données de l'énoncé
        Ltmp = list()
        L2tmp = list()
        L3tmp = list()
        for e in s:
            for f in Symb:
                if e in kwargs and f.name==e:
                    val = kwargs[e]
                    Ltmp.append((f, val))
                    L2tmp.append((e, val))
                elif f.name==e:
                    L3tmp.append((e, "…"))
        self.known = dict(Ltmp)
        self.known_names = dict(L2tmp)
        self.probas = dict(L2tmp)
        # inconnues:
        self.unknown = [s for s in Symb if s.name not in kwargs]
        self.unknown_names = dict(L3tmp)
        # poids pour énoncé
        self.prob_énoncé = dict(L2tmp)
        self.prob_énoncé.update(self.unknown_names)
        # poids … pour énoncé complètement vide
        self.prob_énoncé_vide = {e:"…" for e in s}

        # système des contraintes
        if "indep" not in kwargs:
            self.SYS =[Eq(a+ca,1), Eq(b+cb,1), Eq(ab+cab, b), Eq(ab+acb,a),
                       Eq(acb+cacb, cb), Eq(cab+cacb, ca), Eq(a_b+ca_b, 1),
                       Eq(a_cb+ca_cb, 1), Eq(b_a+cb_a,1), Eq(b_ca+cb_ca, 1),
                       Eq(a*b_a, ab), Eq(a*cb_a, acb), Eq(ca*b_ca, cab),
                       Eq(ca*cb_ca, cacb), Eq(b*a_b, ab), Eq(b*ca_b, cab),
                       Eq(cb*a_cb, acb), Eq(cb*ca_cb, cacb)]
        else:
            self.SYS =[Eq(a+ca,1), Eq(b+cb,1), Eq(ab+cab, b), Eq(ab+acb,a),
                       Eq(acb+cacb, cb), Eq(cab+cacb, ca), Eq(a_b+ca_b, 1),
                       Eq(a_cb+ca_cb, 1), Eq(b_a+cb_a,1), Eq(b_ca+cb_ca, 1),
                       Eq(a*b_a, ab), Eq(a*cb_a, acb), Eq(ca*b_ca, cab),
                       Eq(ca*cb_ca, cacb), Eq(b*a_b, ab), Eq(b*ca_b, cab),
                       Eq(cb*a_cb, acb), Eq(cb*ca_cb, cacb), Eq(a*b, ab),
                       Eq(a*cb,acb), Eq(ca*b,cab), Eq(ca*cb, cacb)]
        # màj des valeurs connues
        self.SYS = [ E.subs(self.known) for E in self.SYS]
        self.noms = list(symbols("A B"))
        if "noms" in kwargs:
            self.noms[0].name = kwargs["noms"][0]
            self.noms[1].name = kwargs["noms"][1]

        # essai infructueux conjugate pour ca cb
        #self.titres = {"a": self.noms[0], "ca": conjugate(self.noms[0]),
        #               "b": self.noms[1], "cb": conjugate(self.noms[1])}

        self.titres = {"a": f"<B>{self.noms[0].name}</B>",
                       "ca": f"<B><O>{self.noms[0].name}</O></B>",
                       "b": f"<B>{self.noms[1].name}</B>",
                       "cb": f"<B><O>{self.noms[1].name}</O></B>"}

        # dictionnaire des rendus web
        self.r = {"mathml": print_mathml, "latex": self._latex, "str": str,
                  "choice": self._format} 
        
        # dictionnaire de résolution complète: self.probas
        # auparavant les valeurs inconnues sont remplacées par "…"
        solstmp = solve(self.SYS, self.unknown, dict=True)[0]
        dtmp = {k.name: v for k,v in solstmp.items()}
        self.probas.update(dtmp)
        
        if "a" in kwargs or "ca" in kwargs:
            self.makeGrapheviz(1, prob=self.probas)
        elif "b" in kwargs or "cb" in kwargs: #précaution test elif
            self.makeGrapheviz(2, prob=self.probas)

    def _wrap_gv(self, **kwargs):
        """générateur d'arbre graphviz
        """
        KW = dict({"intersection":False, "mode":'full', "render": "str",
                   "prob":self.probas})
        KW.update(kwargs)
        if "a" in self.known_names or "ca" in self.known_names:
            self.makeGrapheviz(1, **KW)
        #précaution test elif
        elif "b" in self.known_names or "cb" in self.known_names: 
            self.makeGrapheviz(2, **KW)
            
    def enonce(self, **kwargs):
        """générer un arbre d'énoncé
        """
        KW = dict({"intersection":False, "mode":'full', "render": "choice",
                   "prob":self.prob_énoncé})
        KW.update(kwargs)
        self._wrap_gv(**KW)

    def enonce_vide(self, **kwargs):
        """générer un arbre d'énoncé avec que des '…'
        """
        KW = dict({"intersection":False, "mode":'full', "render": "choice",
                   "prob":self.prob_énoncé_vide})
        KW.update(kwargs)
        self._wrap_gv(**KW)
            
    def solution(self, **kwargs):
        """générer un arbre complété
        """
        KW = dict({"intersection":False, "mode":'full', "render": "choice",
                   "prob":self.probas})
        KW.update(kwargs)
        self._wrap_gv(**KW)
            
    def _format(self, n):
        """générer correctement la string d'une probabilité

        en pourcentage, en fraction standard, en décimal
        précision adaptée à la situation: max des chiffres après virg 
        dans les données
        :param n: (nombre sympy Rational ou float) ou "…"
        :rtype: str
        """
        if n == "…":
            return n
        else: # .format veut des vrais float
            if self.nbformat == "fraction":
                return f"{n}" # aucun traitement, géré par sympy
            elif self.nbformat == "pourcentage":
                return (f"{{:#.{self.precision-2}%}}").format(float(n))
            elif self.nbformat == "decimal":
                return (f"{{:#.{self.precision}f}}").format(float(n))
        
    def _latex(self,p):
        return r"\({}\)".format(latex(p))
    
    def makeGrapheviz(self, num, intersection=True, mode='full', render="str",
                      prob=None):
        """construction de l'arbre pondéré 

        partant de la variable 1 ou 2
        1: a puis b
        2: b puis a

        :param intersection: indique si on remplit la probabilité de
            l'intersection en bout de branche quand elle est connue
        :type intersection: bool
        :param mode: in ['full', 'partial'] full: indique si on doit afficher 
             toutes les probas d'intersection 
             (éventuellement avec des … de recherche)
             partial: on n'affiche que les intersections connues, 
             et rien ailleurs
        :param prob: dict des probabilités
        :type prob: dict
        :rtype: None
        """
        dot = Digraph(comment="arbre pondéré",
                      node_attr={"shape":"plaintext"})
        dot.attr("graph",rankdir="LR",splines="line")
        dot.format ="png" # "svg"

        # homogeneite level 0
        z = symbols('z')
        z.name="."
        level ={1: ["a","ca"], 2: ["b","cb"]}            
        # création des sous-graphes par niveau
        N=0
        with dot.subgraph(name=f"cluster_{N}",
                          node_attr={'rank': 'same'}) as c:
            c.attr(style="invis") # désactivation du cadre de cluster
            c.node("&#160;")
        N=1
        with dot.subgraph(name=f"cluster_{N}",
                          node_attr={'rank': 'same'}) as c:
            c.attr(style="invis") # désactivation du cadre de cluster
            for e in level[num]:
                c.node(e, f"<{latex(self.titres[e])}>")
                # la str html doit être encadrée de <>
        N=2
        #L2 = list()
        with dot.subgraph(name=f"cluster_{N}",
                          node_attr={'rank': 'same'}) as c:
            c.attr(style="invis") # désactivation du cadre de cluster
            for e in level[num]:
                for f in level[(3-num)]:
                    nom = f"{f}_{e}"
                    tmp = (e+f if e+f in self.probas else f+e)
                    # formatage de la proba de l'intersection
                    if self.nbformat=='pourcentage' and prob[tmp] != "…":
                        if tmp in self.known_names:#le param doit être un float
                            preci = len(str(float(prob[tmp])).partition(".")[2])
                            p = (f"{{:#.{preci-2}%}}").format(float(prob[tmp]))
                        else:
                            p = (f"{{:#.{2*self.precision-2}%}}").format(float(prob[tmp])) 
                    elif self.nbformat=='decimal' and prob[tmp] !="…":
                        if tmp in self.known_names:
                            preci = len(str(float(prob[tmp])).strip(".")[2])
                            p = (f"{{:#.{preci}f}}").format(float(prob[tmp]))
                        else:
                            p = (f"{{:#.{2*self.precision}f}}").format(float(prob[tmp]))
                    elif self.nbformat=='decimal' and prob[tmp] !="…":
                        p = str(prob[tmp])
                    elif self.nbformat=='fraction':
                        p = str(prob[tmp])
                    else:
                        p = "…"
                        
                    if mode == 'partial' and prob[tmp] != "…" and tmp in self.known_names:     
                        LAB = '<<TABLE ALIGN="LEFT" BORDER="0" CELLBORDER="0" CELLSPACING="4"><TR><TD>{}</TD><TD>{}</TD></TR></TABLE>>'
                        c.node(nom, LAB.format(self.titres[f], p))
                    elif intersection and mode=='full':     
                        LAB = '<<TABLE ALIGN="LEFT" BORDER="0" CELLBORDER="0" CELLSPACING="4"><TR><TD>{}</TD><TD>{}</TD></TR></TABLE>>'
                        c.node(nom, LAB.format(self.titres[f], p))
                    else: # une case sans la proba d'intersection
                        c.node(nom, '<<TABLE ALIGN="LEFT" BORDER="0" CELLBORDER="0" CELLSPACING="4"><TR><TD>{}</TD><TD>&#160;&#160;&#160;&#160;</TD></TR></TABLE>>'.format(self.titres[f]))
        # edges
        for e in level[num]:
            dot.edge("&#160;", e, label=f"{self.r[render](prob[e])}",
                     arrowhead="none")
        for c in [(level[num], level[3-num])]:
            for a in c[0]:
                for b in c[1]:
                    nom = f"{b}_{a}"
                    dot.edge(a, nom, label=f"{self.r[render](prob[nom])}",
                             arrowhead="none")
        self.gv = dot
