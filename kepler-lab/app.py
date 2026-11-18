import numpy as np
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Kepler Lab", layout="wide")
st.title("Kepler Lab — A lei das áreas")
st.write("Investigue como a velocidade orbital varia enquanto áreas iguais são varridas em tempos iguais.")
a = st.sidebar.slider("Semieixo maior (UA)", 0.5, 5.0, 1.0, 0.1)
e = st.sidebar.slider("Excentricidade", 0.0, 0.9, 0.6, 0.05)
n = st.sidebar.slider("Intervalos iguais de tempo", 4, 24, 12)
k = st.sidebar.slider("Intervalo selecionado", 1, n, 1)
b = a * np.sqrt(1-e*e)
def pos(M):
    M = np.asarray(M, dtype=float)
    E = M.copy()
    for _ in range(60):
        delta = (E-e*np.sin(E)-M)/(1-e*np.cos(E))
        E -= delta
        if np.max(np.abs(delta)) < 1e-12:
            break
    return a*(np.cos(E)-e), b*np.sin(E), E
edges = np.linspace(0, 2*np.pi, n+1)
x,y,_ = pos(np.linspace(0,2*np.pi,1000))
fig = go.Figure()
fig.add_scatter(x=x,y=y,mode="lines",name="Órbita",line=dict(color="#64748b"))
areas=[]
for i in range(n):
    xx,yy,ee=pos(np.linspace(edges[i],edges[i+1],150))
    area=a*b/2*((ee[-1]-ee[0])-e*(np.sin(ee[-1])-np.sin(ee[0])))
    areas.append(area)
    if i == k-1:
        fig.add_scatter(x=np.r_[0,xx,0],y=np.r_[0,yy,0],fill="toself",mode="lines",name="Setor selecionado",fillcolor="rgba(37,99,235,.35)",line=dict(color="#2563eb"))
    else:
        fig.add_scatter(x=[0,xx[0]],y=[0,yy[0]],mode="lines",line=dict(color="#94a3b8",width=1),showlegend=False)
fig.add_scatter(x=[0],y=[0],mode="markers",marker=dict(size=18,color="#f59e0b"),name="Sol (foco)")
px,py,_=pos(np.array([(edges[k-1]+edges[k])/2]))
fig.add_scatter(x=px,y=py,mode="markers",marker=dict(size=13,color="#2563eb"),name="Planeta")
fig.update_layout(yaxis=dict(scaleanchor="x",scaleratio=1),xaxis_title="x (UA)",yaxis_title="y (UA)",height=560)
st.plotly_chart(fig,use_container_width=True)
r=float(np.hypot(px[0],py[0]))
period=a**1.5
speed=29.7847*np.sqrt(2/r-1/a)
c1,c2,c3=st.columns(3)
c1.metric("Área do setor (UA²)",f"{areas[k-1]:.5f}")
c2.metric("Velocidade (km/s)",f"{speed:.2f}")
c3.metric("Período (anos)",f"{period:.3f}")
st.bar_chart({"Área (UA²)":areas})
st.write("Área teórica de cada setor: ",float(np.pi*a*b/n))
st.latex(r"A=\frac{ab}{2}(E-e\sin E)")
st.write("A diferença dessa expressão nos extremos do intervalo fornece a área varrida. A anomalia média cresce uniformemente no tempo, por isso os setores têm áreas iguais.")
st.caption("Modelo ideal de dois corpos, com massa solar dominante. Unidades astronômicas e anos terrestres; sem perturbações. Autoria do projeto: Joice Souza Martins Santos — Matemática & Contexto.")
