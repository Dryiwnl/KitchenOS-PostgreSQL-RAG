import { FormEvent, useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  BookOpen,
  Boxes,
  ChefHat,
  CircleDollarSign,
  Database,
  LayoutDashboard,
  PackagePlus,
  Pencil,
  Orbit,
  RefreshCw,
  Search,
  ShoppingBag,
  Trash2,
  TrendingUp,
  Users,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import Plot from "react-plotly.js";
import "./chat.css";
import "./embeddings.css";
import "./academic.css";
import { acompanharPonteiro, alternarSelecao, concluirClique, iniciarClique, type InicioClique } from "./embeddingInteraction";

const API = "http://127.0.0.1:8000";

type Pagina = "dashboard" | "estoque" | "receitas" | "descoberta" | "explorer" | "vendas" | "perdas" | "analytics" | "dados" | "admin";
type Registro = Record<string, string | number | null>;

type Produto = {
  cod_produto: number;
  nome: string;
  estoque: number;
  unidade_medida: string;
  estoque_minimo: number;
  fator_correcao: number;
};

type Dashboard = {
  indicadores: {
    faturamento: number;
    pedidos_pagos: number;
    produtos_abaixo_minimo: number;
    quantidade_perdida: number;
  };
  receitas_mais_vendidas: Registro[];
  vendas_por_periodo: Registro[];
};

type Ficha = {
  receita: Registro;
  ingredientes_diretos: Registro[];
  subreceitas: Registro[];
  ingredientes_expandidos: Registro[];
  custo_total: number | null;
  custo_unitario: number | null;
  margem_unitaria: number | null;
  ingredientes_sem_preco: number;
};

async function api<T>(caminho: string, opcoes?: RequestInit): Promise<T> {
  const resposta = await fetch(`${API}${caminho}`, {
    headers: { "Content-Type": "application/json" },
    ...opcoes,
  });
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => ({}));
    throw new Error(corpo.detail || `Erro ${resposta.status}`);
  }
  if (resposta.status === 204) return undefined as T;
  return resposta.json();
}

const moeda = (valor: unknown) =>
  Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

function EstadoErro({ mensagem, tentar }: { mensagem: string; tentar: () => void }) {
  return (
    <div className="error-state">
      <AlertTriangle size={28} />
      <div>
        <strong>Não foi possível carregar os dados</strong>
        <p>{mensagem}</p>
      </div>
      <button className="button secondary" onClick={tentar}><RefreshCw size={16} /> Tentar novamente</button>
    </div>
  );
}

function DashboardPage() {
  const [dados, setDados] = useState<Dashboard | null>(null);
  const [erro, setErro] = useState("");
  const carregar = () => {
    setErro("");
    api<Dashboard>("/dashboard").then(setDados).catch((e) => setErro(e.message));
  };
  useEffect(() => { void carregar(); }, []);
  if (erro) return <EstadoErro mensagem={erro} tentar={carregar} />;
  if (!dados) return <div className="loading">Carregando indicadores...</div>;
  const cards = [
    ["Faturamento", moeda(dados.indicadores.faturamento), CircleDollarSign, "green"],
    ["Pedidos pagos", dados.indicadores.pedidos_pagos, ShoppingBag, "orange"],
    ["Estoque crítico", dados.indicadores.produtos_abaixo_minimo, Boxes, "red"],
    ["Perdas registradas", Number(dados.indicadores.quantidade_perdida).toFixed(3), AlertTriangle, "purple"],
  ] as const;
  return <>
    <div className="page-heading"><div><span className="eyebrow">VISÃO GERAL</span><h1>Dashboard operacional</h1><p>Indicadores calculados diretamente no PostgreSQL.</p></div><div className="live"><span /> Dados reais</div></div>
    <div className="metric-grid">{cards.map(([titulo, valor, Icone, cor]) => <article className="metric" key={titulo}><div className={`metric-icon ${cor}`}><Icone size={20}/></div><span>{titulo}</span><strong>{valor}</strong><small>Base atual do restaurante</small></article>)}</div>
    <div className="chart-grid">
      <article className="panel"><div className="panel-title"><div><span>DESEMPENHO</span><h2>Faturamento mensal</h2></div><TrendingUp size={20}/></div><div className="chart"><ResponsiveContainer><AreaChart data={dados.vendas_por_periodo}><defs><linearGradient id="orange" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#ff7a1a" stopOpacity={.5}/><stop offset="100%" stopColor="#ff7a1a" stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="#242428" vertical={false}/><XAxis dataKey="periodo" stroke="#74747e"/><YAxis stroke="#74747e"/><Tooltip contentStyle={{background:"#151518",border:"1px solid #2a2a30"}} formatter={(v) => moeda(v)}/><Area type="monotone" dataKey="faturamento" stroke="#ff7a1a" fill="url(#orange)" strokeWidth={3}/></AreaChart></ResponsiveContainer></div></article>
      <article className="panel"><div className="panel-title"><div><span>POPULARIDADE</span><h2>Receitas mais vendidas</h2></div><BarChart3 size={20}/></div><div className="chart"><ResponsiveContainer><BarChart data={dados.receitas_mais_vendidas} layout="vertical"><CartesianGrid stroke="#242428" horizontal={false}/><XAxis type="number" stroke="#74747e"/><YAxis type="category" dataKey="nome" width={120} stroke="#aaaab3"/><Tooltip contentStyle={{background:"#151518",border:"1px solid #2a2a30"}}/><Bar dataKey="quantidade" fill="#ff7a1a" radius={[0,6,6,0]}/></BarChart></ResponsiveContainer></div></article>
    </div>
  </>;
}

const produtoVazio = { cod_produto: 0, nome: "", estoque: 0, unidade_medida: "kg", estoque_minimo: 0, fator_correcao: 1 };

function EstoquePage() {
  const [produtos, setProdutos] = useState<Produto[]>([]);
  const [form, setForm] = useState<Produto>(produtoVazio);
  const [editando, setEditando] = useState<number | null>(null);
  const [erro, setErro] = useState("");
  const carregar = () => api<Produto[]>("/produtos").then(setProdutos).catch(e => setErro(e.message));
  useEffect(() => { void carregar(); }, []);
  const salvar = async (evento: FormEvent) => {
    evento.preventDefault(); setErro("");
    try {
      await api(editando === null ? "/produtos" : `/produtos/${editando}`, { method: editando === null ? "POST" : "PUT", body: JSON.stringify(form) });
      setForm(produtoVazio); setEditando(null); carregar();
    } catch (e) { setErro((e as Error).message); }
  };
  const editar = (produto: Produto) => { setForm(produto); setEditando(produto.cod_produto); };
  const excluir = async (codigo: number) => { if (!confirm("Excluir este produto?")) return; try { await api(`/produtos/${codigo}`, {method:"DELETE"}); carregar(); } catch(e) { setErro((e as Error).message); } };
  return <>
    <div className="page-heading"><div><span className="eyebrow">ESTOQUE</span><h1>Produtos e ingredientes</h1><p>Cadastre produtos e acompanhe os níveis disponíveis.</p></div></div>
    {erro && <EstadoErro mensagem={erro} tentar={carregar}/>} 
    <div className="split-layout">
      <article className="panel form-panel"><div className="panel-title"><div><span>CADASTRO</span><h2>{editando === null ? "Novo produto" : "Editar produto"}</h2></div><PackagePlus size={20}/></div>
        <form onSubmit={salvar} className="form-grid">
          <label>Código<input type="number" required value={form.cod_produto} onChange={e=>setForm({...form,cod_produto:Number(e.target.value)})}/></label>
          <label>Nome<input required value={form.nome} onChange={e=>setForm({...form,nome:e.target.value})}/></label>
          <label>Estoque<input type="number" step="0.001" min="0" required value={form.estoque} onChange={e=>setForm({...form,estoque:Number(e.target.value)})}/></label>
          <label>Unidade<input required maxLength={10} value={form.unidade_medida} onChange={e=>setForm({...form,unidade_medida:e.target.value})}/></label>
          <label>Estoque mínimo<input type="number" step="0.001" min="0" required value={form.estoque_minimo} onChange={e=>setForm({...form,estoque_minimo:Number(e.target.value)})}/></label>
          <label>Fator de correção<input type="number" step="0.0001" min="1" required value={form.fator_correcao} onChange={e=>setForm({...form,fator_correcao:Number(e.target.value)})}/></label>
          <div className="form-actions"><button className="button primary" type="submit">{editando === null ? "Cadastrar" : "Salvar alterações"}</button>{editando !== null && <button type="button" className="button secondary" onClick={()=>{setEditando(null);setForm(produtoVazio)}}>Cancelar</button>}</div>
        </form>
      </article>
      <article className="panel table-panel"><div className="panel-title"><div><span>INVENTÁRIO</span><h2>{produtos.length} produtos</h2></div></div><div className="table-wrap"><table><thead><tr><th>Produto</th><th>Estoque</th><th>Mínimo</th><th>Situação</th><th></th></tr></thead><tbody>{produtos.map(p=><tr key={p.cod_produto}><td><strong>{p.nome}</strong><small>#{p.cod_produto}</small></td><td>{p.estoque} {p.unidade_medida}</td><td>{p.estoque_minimo}</td><td><span className={`badge ${Number(p.estoque)<Number(p.estoque_minimo)?"danger":"success"}`}>{Number(p.estoque)<Number(p.estoque_minimo)?"Crítico":"Regular"}</span></td><td className="actions"><button onClick={()=>editar(p)}><Pencil size={15}/></button><button onClick={()=>excluir(p.cod_produto)}><Trash2 size={15}/></button></td></tr>)}</tbody></table></div></article>
    </div>
  </>;
}

function ReceitasPage() {
  const [receitas, setReceitas] = useState<Registro[]>([]);
  const [ficha, setFicha] = useState<Ficha | null>(null);
  const [selecionada, setSelecionada] = useState<number | null>(null);
  const [erro, setErro] = useState("");

  const abrirFicha = async (codigo: number) => {
    setSelecionada(codigo); setFicha(null); setErro("");
    try { setFicha(await api<Ficha>(`/receitas/${codigo}/ficha`)); }
    catch (e) { setErro((e as Error).message); }
  };

  useEffect(() => {
    api<Registro[]>("/receitas").then((dados) => {
      setReceitas(dados);
      if (dados.length) void abrirFicha(Number(dados[0].cod_receita));
    }).catch((e) => setErro(e.message));
  }, []);

  return <>
    <div className="page-heading"><div><span className="eyebrow">FICHAS TÉCNICAS</span><h1>Caderno de receitas</h1><p>Ingredientes, sub-receitas, rendimento e custo calculado.</p></div></div>
    {erro && <EstadoErro mensagem={erro} tentar={() => selecionada && void abrirFicha(selecionada)}/>} 
    <div className="recipe-layout">
      <aside className="recipe-index">
        <div className="recipe-index-head"><BookOpen size={18}/><strong>{receitas.length} receitas</strong></div>
        {receitas.map((receita) => <button key={String(receita.cod_receita)} className={selecionada===Number(receita.cod_receita)?"selected":""} onClick={()=>void abrirFicha(Number(receita.cod_receita))}><span>{receita.categoria}</span><strong>{receita.nome}</strong><small>{receita.rendimento} {receita.unidade_de_rendimento} · {moeda(receita.preco_de_venda)}</small></button>)}
      </aside>
      <section className="recipe-sheet">
        {!ficha ? <div className="loading">Abrindo ficha técnica...</div> : <>
          <header className="sheet-header"><div><span>{ficha.receita.categoria}</span><h2>{ficha.receita.nome}</h2><p>{ficha.receita.modo_preparo}</p></div><div className="sheet-price"><small>PREÇO DE VENDA</small><strong>{moeda(ficha.receita.preco_de_venda)}</strong></div></header>
          <div className="sheet-metrics"><div><small>Custo do lote</small><strong>{ficha.custo_total===null?"Sem preço":moeda(ficha.custo_total)}</strong></div><div><small>Custo por {ficha.receita.unidade_de_rendimento}</small><strong>{ficha.custo_unitario===null?"—":moeda(ficha.custo_unitario)}</strong></div><div><small>Margem unitária</small><strong className="positive">{ficha.margem_unitaria===null?"—":moeda(ficha.margem_unitaria)}</strong></div><div><small>Rendimento</small><strong>{ficha.receita.rendimento} {ficha.receita.unidade_de_rendimento}</strong></div></div>
          {ficha.subreceitas.length>0 && <div className="subrecipes"><h3>Sub-receitas utilizadas</h3><div>{ficha.subreceitas.map(s=><span key={String(s.cod_receita)}>{s.nome} · {s.quantidade} {s.unidade_de_rendimento}</span>)}</div></div>}
          <div className="ingredients-title"><h3>Composição completa</h3><span>inclui os ingredientes das sub-receitas</span></div>
          <div className="ingredient-table"><div className="ingredient-row head"><span>Ingrediente</span><span>Quantidade</span><span>Último preço</span><span>Custo</span></div>{ficha.ingredientes_expandidos.map((item)=><div className="ingredient-row" key={String(item.nome)}><strong>{item.nome}</strong><span>{Number(item.quantidade).toFixed(3)} {item.unidade_medida}</span><span>{item.preco_unitario===null?"Sem compra":moeda(item.preco_unitario)}</span><span>{item.custo===null?"—":moeda(item.custo)}</span></div>)}</div>
        </>}
      </section>
    </div>
  </>;
}

function DescobertaPage() {
  const [status, setStatus] = useState<Registro | null>(null);
  const [pergunta, setPergunta] = useState("Quero um prato com tomate e queijo");
  const [resultados, setResultados] = useState<Registro[]>([]);
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState("");
  const carregarStatus = () => api<Registro>("/embeddings").then(setStatus).catch(e=>setErro(e.message));
  useEffect(()=>{void carregarStatus()},[]);
  const gerar = async () => { setOcupado(true);setErro("");try{await api("/embeddings/gerar",{method:"POST"});await carregarStatus()}catch(e){setErro((e as Error).message)}finally{setOcupado(false)} };
  const buscar = async (e:FormEvent) => {e.preventDefault();setOcupado(true);setErro("");try{const r=await api<{resultados:Registro[]}>("/embeddings/buscar",{method:"POST",body:JSON.stringify({pergunta,limite:5})});setResultados(r.resultados)}catch(e){setErro((e as Error).message)}finally{setOcupado(false)}};
  return <><div className="page-heading"><div><span className="eyebrow">BUSCA SEMÂNTICA</span><h1>Descoberta de receitas</h1><p>Pesquisa por significado usando os embeddings reais das fichas técnicas.</p></div></div>{erro&&<EstadoErro mensagem={erro} tentar={carregarStatus}/>}<div className="semantic-hero"><div><Search size={24}/><h2>O que você quer preparar?</h2><p>Descreva uma ideia, estilo ou ingrediente. A busca compara sua frase com os vetores das receitas.</p></div><div className="embedding-status"><span>{Number(status?.quantidade||0)>0?"Índice pronto":"Índice vazio"}</span><strong>{status?.quantidade||0} receitas · {status?.dimensao||384} dimensões</strong><small>{String(status?.modelo_configurado||"")}</small><button className="button secondary" disabled={ocupado} onClick={()=>void gerar()}>{ocupado?"Processando...":"Gerar ou atualizar embeddings"}</button></div></div><form className="semantic-search" onSubmit={buscar}><input value={pergunta} onChange={e=>setPergunta(e.target.value)} minLength={3} placeholder="Ex.: prato leve com tomate para o verão"/><button className="button primary" disabled={ocupado}><Search size={17}/>{ocupado?"Buscando...":"Buscar receitas"}</button></form><div className="semantic-results">{resultados.map((r,i)=><article key={String(r.cod_receita)}><div className="result-rank">{String(i+1).padStart(2,"0")}</div><div><span>{r.categoria}</span><h3>{r.nome}</h3><p>{r.texto}</p></div><div className="similarity"><strong>{(Number(r.similaridade)*100).toFixed(1)}%</strong><small>similaridade</small><i style={{width:`${Number(r.similaridade)*100}%`}}/></div></article>)}</div></>;
}

type PontoEmbedding = {
  cod_receita:number; nome:string; categoria:string; texto:string;
  modelo:string; dimensao:number; x:number; y:number; z:number;
  vizinhos:{nome:string;similaridade:number}[];
};

function ExplorerPage() {
  const [dados,setDados]=useState<{metodo:string;variancia_explicada:number[];pontos:PontoEmbedding[]} | null>(null);
  const [selecionado,setSelecionado]=useState<PontoEmbedding | null>(null);
  const [erro,setErro]=useState("");
  const carregar=()=>api<{metodo:string;variancia_explicada:number[];pontos:PontoEmbedding[]}>("/embeddings/explorer").then((r)=>{setDados(r);if(r.pontos.length)setSelecionado(r.pontos[0])}).catch(e=>setErro(e.message));
  useEffect(()=>{void carregar()},[]);
  const cores:Record<string,string>={"Bases e molhos":"#bd5a32","Pratos principais":"#315d46","Lanches":"#d19a3e","Sobremesas":"#8a6479"};
  const clicar=(evento:any)=>{const ponto=evento.points?.[0]?.customdata as PontoEmbedding|undefined;if(ponto)setSelecionado(ponto)};
  return <><div className="page-heading"><div><span className="eyebrow">EMBEDDING EXPLORER</span><h1>Mapa semântico das receitas</h1><p>Projeção tridimensional dos vetores originais usando PCA.</p></div></div>{erro&&<EstadoErro mensagem={erro} tentar={carregar}/>} {!dados?<div className="loading">Calculando projeção...</div>:<div className="explorer-layout"><section className="explorer-plot"><div className="projection-note"><Orbit size={18}/><div><strong>{dados.metodo} · 384 → 3 dimensões</strong><small>Variância explicada: {dados.variancia_explicada.map(v=>(v*100).toFixed(1)+"%").join(" · ")}. As distâncias 3D são uma projeção; a busca usa os vetores originais.</small></div></div><Plot data={[{type:"scatter3d",mode:"markers+text",x:dados.pontos.map(p=>p.x),y:dados.pontos.map(p=>p.y),z:dados.pontos.map(p=>p.z),text:dados.pontos.map(p=>p.nome),textposition:"top center",customdata:dados.pontos,hovertemplate:"<b>%{text}</b><br>%{customdata.categoria}<extra></extra>",marker:{size:8,color:dados.pontos.map(p=>cores[p.categoria]||"#777"),line:{width:1,color:"#fff"}}} as any]} layout={{autosize:true,height:540,margin:{l:0,r:0,t:10,b:0},paper_bgcolor:"#fffdf7",plot_bgcolor:"#fffdf7",font:{family:"DM Sans",color:"#4f544b"},scene:{bgcolor:"#fffdf7",xaxis:{title:{text:"PCA 1"},gridcolor:"#ddd6ca"},yaxis:{title:{text:"PCA 2"},gridcolor:"#ddd6ca"},zaxis:{title:{text:"PCA 3"},gridcolor:"#ddd6ca"}}}} config={{responsive:true,displaylogo:false}} style={{width:"100%"}} onClick={clicar}/></section>{selecionado&&<aside className="point-detail"><span>{selecionado.categoria}</span><h2>{selecionado.nome}</h2><p>{selecionado.texto}</p><dl><div><dt>Registro</dt><dd>Receita #{selecionado.cod_receita}</dd></div><div><dt>Modelo</dt><dd>{selecionado.modelo}</dd></div><div><dt>Vetor original</dt><dd>{selecionado.dimensao} dimensões</dd></div></dl><h3>Vizinhos mais próximos</h3><ul>{selecionado.vizinhos.map(v=><li key={v.nome}><strong>{v.nome}</strong><span>{(v.similaridade*100).toFixed(1)}%</span></li>)}</ul></aside>}</div>}</>;
}

type MensagemChat = {
  id:string; papel:"usuario"|"assistente"; texto:string; fontes?:Registro[];
};

function ChatAIPage() {
  const [configurado,setConfigurado]=useState(false);
  const [modelo,setModelo]=useState("");
  const [chave,setChave]=useState("");
  const [pergunta,setPergunta]=useState("");
  const [mensagens,setMensagens]=useState<MensagemChat[]>([]);
  const [ocupado,setOcupado]=useState(false);
  const [erro,setErro]=useState("");

  const carregar=async()=>{
    try {
      const status=await api<{configurado:boolean;modelo:string}>("/chat/status");
      setConfigurado(status.configurado);setModelo(status.modelo);
      const historico=await api<Registro[]>("/chat/historico");
      setMensagens(historico.flatMap((item)=>[
        {id:`u-${item.cod_interacao}`,papel:"usuario" as const,texto:String(item.pergunta)},
        {id:`a-${item.cod_interacao}`,papel:"assistente" as const,texto:String(item.resposta)},
      ]));
    } catch(e){setErro((e as Error).message)}
  };
  useEffect(()=>{void carregar()},[]);

  const configurar=async(e:FormEvent)=>{
    e.preventDefault();setOcupado(true);setErro("");
    try{const r=await api<{configurado:boolean;modelo:string}>("/chat/configurar",{method:"POST",body:JSON.stringify({api_key:chave})});setConfigurado(r.configurado);setModelo(r.modelo);setChave("")}
    catch(e){setErro((e as Error).message)}finally{setOcupado(false)}
  };

  const enviar=async(e:FormEvent)=>{
    e.preventDefault();const texto=pergunta.trim();if(!texto)return;
    const id=Date.now().toString();setMensagens(m=>[...m,{id,papel:"usuario",texto}]);setPergunta("");setOcupado(true);setErro("");
    try{const r=await api<{resposta:string;fontes:Registro[]}>("/chat",{method:"POST",body:JSON.stringify({pergunta:texto})});setMensagens(m=>[...m,{id:`a-${id}`,papel:"assistente",texto:r.resposta,fontes:r.fontes}]);window.dispatchEvent(new Event("chat-atualizado"))}
    catch(e){setErro((e as Error).message)}finally{setOcupado(false)}
  };

  if(!configurado)return <><div className="page-heading"><div><span className="eyebrow">CHAT IA</span><h1>Assistente do restaurante</h1><p>Gemini conectado ao contexto controlado do PostgreSQL.</p></div></div>{erro&&<EstadoErro mensagem={erro} tentar={carregar}/>}<section className="chat-setup"><div><ChefHat size={34}/><h2>Conecte gratuitamente ao Gemini</h2><p>Crie uma chave gratuita no Google AI Studio e cole abaixo. Ela ficará somente no arquivo <code>.env</code> local, ignorado pelo Git.</p><a href="https://aistudio.google.com/apikey" target="_blank" rel="noreferrer">Criar chave no Google AI Studio</a></div><form onSubmit={configurar}><label>Gemini API key<input type="password" value={chave} onChange={e=>setChave(e.target.value)} placeholder="Cole sua chave aqui" minLength={20} required/></label><button className="button primary" disabled={ocupado}>{ocupado?"Configurando...":"Ativar Chat IA"}</button></form></section></>;

  return <><div className="page-heading"><div><span className="eyebrow">CHAT IA · {modelo}</span><h1>Converse com seus dados</h1><p>Pergunte sobre receitas, estoque, compras, custos, clientes, pedidos ou perdas.</p></div></div>{erro&&<EstadoErro mensagem={erro} tentar={carregar}/>}<section className="chat-shell"><div className="chat-messages">{mensagens.length===0&&<div className="chat-welcome"><ChefHat size={35}/><h2>Como posso ajudar?</h2><p>Ex.: “Quais receitas usam tomate?”, “Qual produto teve mais perdas?” ou “O que posso promover com o estoque atual?”</p></div>}{mensagens.map(m=><article key={m.id} className={`chat-message ${m.papel}`}><span>{m.papel==="usuario"?"Você":"Chat IA"}</span><div>{m.texto}</div>{m.fontes&&m.fontes.length>0&&<footer>Fontes semânticas: {m.fontes.map(f=>`${f.nome} (${(Number(f.similaridade)*100).toFixed(1)}%)`).join(" · ")}</footer>}</article>)}{ocupado&&<div className="chat-typing"><i/><i/><i/> Consultando banco e Gemini...</div>}</div><form className="chat-compose" onSubmit={enviar}><textarea value={pergunta} onChange={e=>setPergunta(e.target.value)} placeholder="Faça qualquer pergunta sobre os dados do restaurante..." rows={2}/><button className="button primary" disabled={ocupado||!pergunta.trim()}>Enviar</button></form></section></>;
}

type PontoMapa = {id:string;tipo:"receita"|"consulta";nome:string;categoria:string;texto:string;modelo:string;dimensao:number;x:number;y:number;z:number};
type Comparacao = {similaridade_cosseno:number;angulo_graus:number;distancia_cosseno:number;distancia_euclidiana:number;dimensoes:number};

function nivelSimilaridade(valor:number){
  if(valor>=.8)return "Muito alta";
  if(valor>=.6)return "Alta";
  if(valor>=.4)return "Moderada";
  if(valor>=.2)return "Baixa";
  return "Muito baixa";
}

function DiagramaAngulo({angulo}:{angulo:number}){
  const radianos=angulo*Math.PI/180;
  const origem={x:92,y:92};const tamanho=62;
  const pontoA={x:origem.x+tamanho,y:origem.y};
  const pontoB={x:origem.x+tamanho*Math.cos(radianos),y:origem.y-tamanho*Math.sin(radianos)};
  return <svg className="cosine-angle" viewBox="0 0 190 112" role="img" aria-label={`Ângulo exato de ${angulo.toFixed(2)} graus no espaço original`}>
    <line x1={origem.x} y1={origem.y} x2={pontoA.x} y2={pontoA.y} className="angle-vector first"/>
    <line x1={origem.x} y1={origem.y} x2={pontoB.x} y2={pontoB.y} className="angle-vector second"/>
    <circle cx={origem.x} cy={origem.y} r="3" className="angle-origin"/>
    <circle cx={pontoA.x} cy={pontoA.y} r="4" className="angle-first"/>
    <circle cx={pontoB.x} cy={pontoB.y} r="4" className="angle-second"/>
    <text x="8" y="18">Ângulo em 384D</text>
    <text x="8" y="38" className="angle-value">{angulo.toFixed(2)}°</text>
  </svg>;
}

function EmbeddingsPage() {
  const [dados,setDados]=useState<{metodo:string;variancia_explicada:number[];pontos:PontoMapa[]} | null>(null);
  const [selecionados,setSelecionados]=useState<PontoMapa[]>([]);
  const [comparacao,setComparacao]=useState<Comparacao|null>(null);
  const [erro,setErro]=useState("");
  const [cameraVersao,setCameraVersao]=useState(0);
  const cameraRef=useRef<any>({eye:{x:1.45,y:1.45,z:1.15},center:{x:0,y:0,z:0},up:{x:0,y:0,z:1}});
  const hoverPontoRef=useRef<PontoMapa|undefined>(undefined);
  const gestoRef=useRef<InicioClique<PontoMapa>|undefined>(undefined);
  const carregar=()=>api<{metodo:string;variancia_explicada:number[];pontos:PontoMapa[]}>("/embeddings/explorer").then(setDados).catch(e=>setErro(e.message));
  useEffect(()=>{void carregar();const ouvir=()=>void carregar();window.addEventListener("chat-atualizado",ouvir);return()=>window.removeEventListener("chat-atualizado",ouvir)},[]);
  useEffect(()=>{if(selecionados.length===2){api<Comparacao>("/embeddings/comparar",{method:"POST",body:JSON.stringify({primeiro:selecionados[0].id,segundo:selecionados[1].id})}).then(setComparacao).catch(e=>setErro(e.message))}else setComparacao(null)},[selecionados]);
  const cores:Record<string,string>={receita:"#bd5a32",consulta:"#315d46"};
  const alternar=(p:PontoMapa)=>setSelecionados(atual=>alternarSelecao(atual,p));
  const pontoEvento=(evento:any)=>evento.points?.[0]?.customdata as PontoMapa|undefined;
  const vetorProjetado=(p:PontoMapa|undefined,cor:string)=>({type:"scatter3d",mode:"lines",x:p?[0,p.x]:[],y:p?[0,p.y]:[],z:p?[0,p.z]:[],customdata:p?[p,p]:[],hoverinfo:"none",showlegend:false,line:{width:7,color:cor}});
  const destaque=(p:PontoMapa|undefined,cor:string)=>({type:"scatter3d",mode:"markers+text",x:p?[p.x]:[],y:p?[p.y]:[],z:p?[p.z]:[],text:p?[p.nome]:[],customdata:p?[p]:[],textposition:"top center",textfont:{size:12,color:cor},hoverinfo:"none",showlegend:false,marker:{size:9,color:cor,line:{width:3,color:"#172e25"}}});
  const ligacao=selecionados.length===2?{type:"scatter3d",mode:"lines",x:selecionados.map(p=>p.x),y:selecionados.map(p=>p.y),z:selecionados.map(p=>p.z),hoverinfo:"none",showlegend:false,line:{width:7,color:"#7d8f84",dash:"dash"}}:{type:"scatter3d",mode:"lines",x:[],y:[],z:[],hoverinfo:"none",showlegend:false};
  const origemPca={type:"scatter3d",mode:"markers+text",x:[0],y:[0],z:[0],text:["Origem PCA (0, 0, 0)"],textposition:"bottom center",textfont:{size:10,color:"#59655e"},hovertemplate:"<b>Origem da projeção PCA</b><br>(0, 0, 0)<extra></extra>",showlegend:false,marker:{size:6,color:"#172e25",symbol:"circle",line:{width:2,color:"#fffdf7"}}};
  const traces:any[] = dados ? [
    {type:"scatter3d",mode:"markers",name:"",showlegend:false,x:dados.pontos.map(p=>p.x),y:dados.pontos.map(p=>p.y),z:dados.pontos.map(p=>p.z),text:dados.pontos.map(p=>`${p.tipo==="consulta"?"Consulta":"Receita"}: ${p.nome}`),customdata:dados.pontos,hovertemplate:"<b>%{text}</b><br>Vetor: [%{x:.4f}, %{y:.4f}, %{z:.4f}]<extra></extra>",marker:{size:12,color:dados.pontos.map(p=>cores[p.tipo]),symbol:dados.pontos.map(p=>p.tipo==="consulta"?"diamond":"circle"),line:{width:2,color:dados.pontos.map(p=>selecionados.some(s=>s.id===p.id)?"#13291f":"#fff")}}},
    origemPca,
    ligacao,
    vetorProjetado(selecionados[0],"#315d46"),
    vetorProjetado(selecionados[1],"#bd5a32"),
    destaque(selecionados[0],"#315d46"),
    destaque(selecionados[1],"#bd5a32"),
  ] : [];
  const limite=dados?.pontos.reduce((maior,p)=>Math.max(maior,Math.abs(p.x),Math.abs(p.y),Math.abs(p.z)),.1)??1;
  const faixa=[-limite*1.2,limite*1.2];
  const restaurarCamera=()=>{
    cameraRef.current={eye:{x:1.45,y:1.45,z:1.15},center:{x:0,y:0,z:0},up:{x:0,y:0,z:1}};
    setCameraVersao(versao=>versao+1);
  };
  return <>
    <div className="page-heading"><div><span className="eyebrow">EMBEDDINGS</span><h1>Espaço vetorial das conversas</h1><p>O mapa cresce conforme você conversa com o Chat IA.</p></div></div>
    {erro&&<EstadoErro mensagem={erro} tentar={carregar}/>} 
    {!dados?<div className="loading">Calculando projeção...</div>:dados.pontos.length===0?
      <section className="embedding-empty"><Orbit size={42}/><h2>Nenhum ponto ainda</h2><p>Faça uma pergunta no Chat IA. A pergunta e as receitas recuperadas aparecerão aqui.</p></section>:
      <>
        <div className="embedding-workspace">
          <section className="explorer-plot">
            <div className="projection-note"><Orbit size={18}/><div><strong>{dados.metodo} · 384 → 3 dimensões · {(dados.variancia_explicada.reduce((soma,v)=>soma+v,0)*100).toFixed(1)}% preservado</strong><small>Os vetores saem do ponto marcado “Origem PCA”. O ângulo visual é aproximado; a comparação válida em 384D está no diagrama abaixo.</small></div><button className="map-reset-button" type="button" onClick={restaurarCamera}><RefreshCw size={14}/> Restaurar posição</button></div>
            <div
              className="embedding-plot-input"
              onPointerDownCapture={evento=>{gestoRef.current=iniciarClique(evento.clientX,evento.clientY,hoverPontoRef.current)}}
              onPointerMoveCapture={evento=>{if(gestoRef.current)gestoRef.current=acompanharPonteiro(gestoRef.current,evento.clientX,evento.clientY)}}
              onPointerUpCapture={()=>{const ponto=concluirClique(gestoRef.current);gestoRef.current=undefined;if(ponto)alternar(ponto)}}
              onPointerCancelCapture={()=>{gestoRef.current=undefined}}
            >
              <Plot
                data={traces}
                layout={{autosize:true,height:590,uirevision:`embedding-camera-${cameraVersao}`,clickmode:"event",showlegend:false,hovermode:"closest",margin:{l:0,r:0,t:0,b:0},paper_bgcolor:"#fffdf7",font:{family:"DM Sans",color:"#4f544b"},scene:{uirevision:`embedding-camera-${cameraVersao}`,camera:cameraRef.current,dragmode:"orbit",aspectmode:"cube",bgcolor:"#fffdf7",xaxis:{title:{text:"PCA 1"},gridcolor:"#ddd6ca",range:faixa,autorange:false},yaxis:{title:{text:"PCA 2"},gridcolor:"#ddd6ca",range:faixa,autorange:false},zaxis:{title:{text:"PCA 3"},gridcolor:"#ddd6ca",range:faixa,autorange:false}}}}
                config={{responsive:true,displaylogo:false,scrollZoom:false,displayModeBar:false,doubleClick:false}}
                style={{width:"100%"}}
                onRelayout={evento=>{if((evento as any)["scene.camera"])cameraRef.current=(evento as any)["scene.camera"]}}
                onHover={evento=>{hoverPontoRef.current=pontoEvento(evento)}}
                onUnhover={()=>{hoverPontoRef.current=undefined}}
              />
            </div>
          </section>
          <aside className="embedding-index">
            <div><span>LEGENDA DO MAPA</span><h2>Pontos</h2><p><i className="dot receita"/> Receitas <i className="dot consulta"/> Perguntas</p></div>
            <div className="embedding-point-list">{dados.pontos.map(p=><button key={p.id} className={selecionados.some(s=>s.id===p.id)?"selected":""} onClick={()=>alternar(p)}><i className={`dot ${p.tipo}`}/><span><small>{p.tipo}</small><strong>{p.nome}</strong></span></button>)}</div>
          </aside>
        </div>
        <section className="vector-legend">
          <div className="selected-vectors">{selecionados.map((p,i)=><article key={p.id} onClick={()=>alternar(p)} title="Clique para desselecionar"><span>Vetor {i+1} · {p.tipo}</span><strong>{p.nome}</strong><code>Projeção PCA: ({p.x.toFixed(5)}, {p.y.toFixed(5)}, {p.z.toFixed(5)})</code></article>)}{selecionados.length<2&&<p>Selecione {2-selecionados.length} ponto(s) para comparar.</p>}</div>
          {comparacao&&<div className="comparison-exact"><div className="comparison-copy"><span>COMPARAÇÃO EXATA · {comparacao.dimensoes}D</span><strong>{nivelSimilaridade(comparacao.similaridade_cosseno)}</strong><small>Cosseno não é probabilidade; o gráfico PCA é apenas uma projeção.</small></div><DiagramaAngulo angulo={comparacao.angulo_graus}/><div className="comparison-values"><div><small>Similaridade de cosseno</small><strong>{comparacao.similaridade_cosseno.toFixed(4)}</strong></div><div><small>Equivalente visual</small><strong>{(comparacao.similaridade_cosseno*100).toFixed(2)}%</strong></div><div><small>Distância cosseno</small><strong>{comparacao.distancia_cosseno.toFixed(4)}</strong></div><div><small>Distância euclidiana</small><strong>{comparacao.distancia_euclidiana.toFixed(4)}</strong></div></div></div>}
        </section>
      </>}
  </>;
}

function TabelaPage({ titulo, subtitulo, endpoint, colunas }: { titulo:string; subtitulo:string; endpoint:string; colunas:[string,string][] }) {
  const [dados,setDados]=useState<Registro[]>([]); const [erro,setErro]=useState("");
  const carregar=()=>api<Registro[]>(endpoint).then(setDados).catch(e=>setErro(e.message)); useEffect(()=>{void carregar()},[endpoint]);
  return <><div className="page-heading"><div><span className="eyebrow">KITCHENOS</span><h1>{titulo}</h1><p>{subtitulo}</p></div></div>{erro?<EstadoErro mensagem={erro} tentar={carregar}/>:<article className="panel table-panel"><div className="table-wrap"><table><thead><tr>{colunas.map(([,rotulo])=><th key={rotulo}>{rotulo}</th>)}</tr></thead><tbody>{dados.map((linha,i)=><tr key={i}>{colunas.map(([campo])=><td key={campo}>{campo.includes("preco")||campo==="total"?moeda(linha[campo]):String(linha[campo]??"—")}</td>)}</tr>)}</tbody></table></div></article>}</>;
}

function DadosPage() {
  const [categorias,setCategorias]=useState<Registro[]>([]); const [fornecedores,setFornecedores]=useState<Registro[]>([]); const [erro,setErro]=useState("");
  const carregar=()=>Promise.all([api<Registro[]>("/categorias"),api<Registro[]>("/fornecedores")]).then(([c,f])=>{setCategorias(c);setFornecedores(f)}).catch(e=>setErro(e.message)); useEffect(()=>{void carregar()},[]);
  return <><div className="page-heading"><div><span className="eyebrow">GESTÃO DE DADOS</span><h1>Cadastros auxiliares</h1><p>Categorias e fornecedores utilizados pelo restaurante.</p></div></div>{erro&&<EstadoErro mensagem={erro} tentar={carregar}/>}<div className="chart-grid"><article className="panel"><div className="panel-title"><div><span>CLASSIFICAÇÃO</span><h2>Categorias</h2></div></div><ul className="record-list">{categorias.map(c=><li key={String(c.cod_categoria)}><span>#{c.cod_categoria}</span><strong>{c.nome}</strong></li>)}</ul></article><article className="panel"><div className="panel-title"><div><span>COMPRAS</span><h2>Fornecedores</h2></div></div><ul className="record-list">{fornecedores.map(f=><li key={String(f.cod_fornecedor)}><span>#{f.cod_fornecedor}</span><strong>{f.nome}</strong><small>{f.contato}</small></li>)}</ul></article></div></>;
}

type ColunaMeta = {column_name:string;data_type:string;udt_name:string;nullable:boolean;column_default:string|null;primary_key:boolean;foreign_key:{tabela_referenciada:string;coluna_referenciada:string}|null};
type TabelaMeta = {nome:string;rotulo:string;primary_key:string[];colunas:ColunaMeta[]};

const rotuloCampo=(campo:string)=>campo.replaceAll("_"," ").replace(/\b\w/g,letra=>letra.toUpperCase());

function CrudGeralPage(){
  const [metadados,setMetadados]=useState<TabelaMeta[]>([]);const [tabela,setTabela]=useState("");
  const [registros,setRegistros]=useState<Registro[]>([]);const [form,setForm]=useState<Record<string,string>>({});
  const [chaveOriginal,setChaveOriginal]=useState<Record<string,string|number|null>|null>(null);
  const [erro,setErro]=useState("");const [mensagem,setMensagem]=useState("");const [ocupado,setOcupado]=useState(false);
  const meta=metadados.find(item=>item.nome===tabela);
  const carregarMetadados=()=>api<TabelaMeta[]>("/dados/metadados").then(lista=>{setMetadados(lista);setTabela(atual=>atual||lista[0]?.nome||"")}).catch(e=>setErro(e.message));
  const carregarRegistros=()=>{if(!tabela)return;setErro("");api<Registro[]>(`/dados/${tabela}`).then(setRegistros).catch(e=>setErro(e.message))};
  useEffect(()=>{void carregarMetadados()},[]);useEffect(()=>{void carregarRegistros();setForm({});setChaveOriginal(null)},[tabela]);
  const valorBanco=(coluna:ColunaMeta,valor:string)=>{if(valor==="")return coluna.nullable?null:"";if(coluna.data_type.includes("integer")||coluna.data_type.includes("numeric")||coluna.data_type.includes("decimal"))return Number(valor);return valor};
  const dadosFormulario=()=>Object.fromEntries((meta?.colunas||[]).map(coluna=>[coluna.column_name,valorBanco(coluna,form[coluna.column_name]??"")]));
  const novo=()=>{setChaveOriginal(null);setForm(Object.fromEntries((meta?.colunas||[]).map(c=>[c.column_name,""])));setMensagem("");setErro("")};
  const editar=(registro:Registro)=>{if(!meta)return;setForm(Object.fromEntries(meta.colunas.map(c=>[c.column_name,String(registro[c.column_name]??"")])));setChaveOriginal(Object.fromEntries(meta.primary_key.map(c=>[c,registro[c]])));setMensagem("");setErro("")};
  const salvar=async(evento:FormEvent)=>{evento.preventDefault();if(!meta)return;setOcupado(true);setErro("");try{const dados=dadosFormulario();if(chaveOriginal){await api(`/dados/${tabela}`,{method:"PUT",body:JSON.stringify({chave:chaveOriginal,dados})})}else{await api(`/dados/${tabela}`,{method:"POST",body:JSON.stringify(dados)})}setMensagem(chaveOriginal?"Registro atualizado.":"Registro inserido.");setForm({});setChaveOriginal(null);carregarRegistros()}catch(e){setErro((e as Error).message)}finally{setOcupado(false)}};
  const excluir=async(registro:Registro)=>{if(!meta||!window.confirm("Excluir este registro? As chaves estrangeiras podem impedir a operação."))return;const chave=Object.fromEntries(meta.primary_key.map(c=>[c,registro[c]]));setErro("");try{await api(`/dados/${tabela}`,{method:"DELETE",body:JSON.stringify(chave)});setMensagem("Registro excluído.");carregarRegistros()}catch(e){setErro((e as Error).message)}};
  return <><div className="page-heading"><div><span className="eyebrow">CRUD DAS 14 TABELAS</span><h1>Gestão de dados</h1><p>Inserir, consultar, atualizar e excluir respeitando as restrições do PostgreSQL.</p></div><button className="button primary" onClick={novo}><PackagePlus size={16}/> Novo registro</button></div>{erro&&<EstadoErro mensagem={erro} tentar={carregarRegistros}/>} {mensagem&&<div className="success-message">{mensagem}</div>}<div className="crud-layout"><aside className="table-selector"><label>Tabela<select value={tabela} onChange={e=>setTabela(e.target.value)}>{metadados.map(item=><option key={item.nome} value={item.nome}>{item.rotulo}</option>)}</select></label><div>{metadados.map(item=><button key={item.nome} className={tabela===item.nome?"selected":""} onClick={()=>setTabela(item.nome)}>{item.rotulo}<small>{item.nome}</small></button>)}</div></aside><section className="crud-content">{Object.keys(form).length>0&&meta&&<form className="generic-form" onSubmit={salvar}><div className="generic-form-head"><div><span>{chaveOriginal?"ATUALIZAÇÃO":"INSERÇÃO"}</span><h2>{meta.rotulo}</h2></div><button type="button" onClick={()=>{setForm({});setChaveOriginal(null)}}>×</button></div><div className="generic-fields">{meta.colunas.map(coluna=><label key={coluna.column_name}>{rotuloCampo(coluna.column_name)}{coluna.primary_key&&<small> chave primária</small>}{coluna.foreign_key&&<small> → {coluna.foreign_key.tabela_referenciada}</small>}{coluna.data_type==="text"?<textarea value={form[coluna.column_name]??""} onChange={e=>setForm({...form,[coluna.column_name]:e.target.value})}/>:<input type={coluna.data_type==="date"?"date":coluna.data_type.includes("timestamp")?"datetime-local":coluna.data_type.includes("integer")||coluna.data_type.includes("numeric")?"number":"text"} step="any" required={!coluna.nullable&&!coluna.column_default} value={form[coluna.column_name]??""} onChange={e=>setForm({...form,[coluna.column_name]:e.target.value})}/>}</label>)}</div><div className="generic-actions"><button className="button primary" disabled={ocupado}>{ocupado?"Salvando...":"Salvar no PostgreSQL"}</button><button className="button secondary" type="button" onClick={()=>{setForm({});setChaveOriginal(null)}}>Cancelar</button></div></form>}<article className="panel table-panel"><div className="panel-title"><div><span>{tabela}</span><h2>{registros.length} registros</h2></div></div><div className="table-wrap"><table><thead><tr>{meta?.colunas.map(c=><th key={c.column_name}>{rotuloCampo(c.column_name)}</th>)}<th>Ações</th></tr></thead><tbody>{registros.map((registro,i)=><tr key={i}>{meta?.colunas.map(c=><td key={c.column_name}>{String(registro[c.column_name]??"—")}</td>)}<td className="actions"><button title="Editar" onClick={()=>editar(registro)}><Pencil size={14}/></button><button title="Excluir" onClick={()=>void excluir(registro)}><Trash2 size={14}/></button></td></tr>)}</tbody></table></div></article></section></div></>;
}

type ResultadoConsulta={id:string;titulo:string;colunas:string[];linhas:Registro[]};
const consultasAcademicas=[{id:"custos-receitas",titulo:"Custos e rentabilidade",arquivo:"01_custos_receitas.sql"},{id:"vendas",titulo:"Vendas",arquivo:"02_vendas.sql"},{id:"estoque-perdas",titulo:"Estoque e perdas",arquivo:"03_estoque_perdas.sql"}];

function AnalyticsPage(){
  const [resultados,setResultados]=useState<Record<string,ResultadoConsulta>>({});const [erros,setErros]=useState<Record<string,string>>({});const [ocupado,setOcupado]=useState("");
  const executar=async(id:string)=>{setOcupado(id);setErros(atual=>({...atual,[id]:""}));try{const resultado=await api<ResultadoConsulta>(`/analytics/${id}`,{method:"POST"});setResultados(atual=>({...atual,[id]:resultado}))}catch(e){setErros(atual=>({...atual,[id]:(e as Error).message}))}finally{setOcupado("")}};
  return <><div className="page-heading"><div><span className="eyebrow">CONSULTAS OBRIGATÓRIAS</span><h1>Analytics SQL</h1><p>O sistema lê os três arquivos da pasta database/queries e apresenta tabela e gráfico.</p></div></div><div className="analytics-list">{consultasAcademicas.map(consulta=>{const resultado=resultados[consulta.id];const linhas=resultado?.linhas||[];const colunas=resultado?.colunas||[];const numerica=[...colunas].reverse().find(c=>linhas.some(l=>l[c]!==null&&!Number.isNaN(Number(l[c]))));const rotulo=colunas.find(c=>c!==numerica)||colunas[0];const grafico=linhas.map(l=>({rotulo:String(l[rotulo]??""),valor:Number(l[numerica||""]||0)}));return <article className="panel analytics-card" key={consulta.id}><div className="analytics-head"><div><span>{consulta.arquivo}</span><h2>{consulta.titulo}</h2></div><button className="button primary" onClick={()=>void executar(consulta.id)} disabled={ocupado===consulta.id}><BarChart3 size={15}/>{ocupado===consulta.id?"Executando...":"Executar SQL"}</button></div>{erros[consulta.id]&&<div className="query-pending"><AlertTriangle size={17}/>{erros[consulta.id]}</div>}{resultado&&<div className="analytics-result"><div className="table-wrap"><table><thead><tr>{colunas.map(c=><th key={c}>{rotuloCampo(c)}</th>)}</tr></thead><tbody>{linhas.map((linha,i)=><tr key={i}>{colunas.map(c=><td key={c}>{String(linha[c]??"—")}</td>)}</tr>)}</tbody></table></div>{numerica&&rotulo&&<div className="query-chart"><ResponsiveContainer width="100%" height={280}><BarChart data={grafico}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="rotulo"/><YAxis/><Tooltip/><Bar dataKey="valor" fill="#bd5a32" radius={[5,5,0,0]}/></BarChart></ResponsiveContainer></div>}</div>}</article>})}</div></>;
}

function AdministracaoPage(){
  const [criar,setCriar]=useState("");const [eliminar,setEliminar]=useState("");const [mensagem,setMensagem]=useState("");const [erro,setErro]=useState("");const [ocupado,setOcupado]=useState(false);
  const executar=async(tipo:"inicializar"|"eliminar",confirmacao:string)=>{setOcupado(true);setErro("");setMensagem("");try{const r=await api<{mensagem:string}>(`/administracao/${tipo}`,{method:"POST",body:JSON.stringify({confirmacao})});setMensagem(r.mensagem)}catch(e){setErro((e as Error).message)}finally{setOcupado(false)}};
  return <><div className="page-heading"><div><span className="eyebrow">AMBIENTE DE DEMONSTRAÇÃO</span><h1>Administração do banco</h1><p>Criação, carga inicial e eliminação das tabelas exigidas pelo trabalho.</p></div></div>{erro&&<EstadoErro mensagem={erro} tentar={()=>setErro("")}/>} {mensagem&&<div className="success-message">{mensagem}</div>}<div className="admin-grid"><article className="panel admin-card"><Database size={28}/><h2>Criar e popular</h2><p>Usa o DDL e os dados iniciais do projeto. Esta opção funciona quando o banco está sem as tabelas.</p><label>Digite <strong>CRIAR</strong><input value={criar} onChange={e=>setCriar(e.target.value)}/></label><button className="button primary" disabled={ocupado||criar!=="CRIAR"} onClick={()=>void executar("inicializar",criar)}>Criar tabelas e carregar dados</button></article><article className="panel admin-card danger-zone"><Trash2 size={28}/><h2>Eliminar todas as tabelas</h2><p>Remove as 14 tabelas acadêmicas e as duas tabelas auxiliares de IA. Esta ação apaga todos os dados.</p><label>Digite <strong>ELIMINAR</strong><input value={eliminar} onChange={e=>setEliminar(e.target.value)}/></label><button className="button danger-button" disabled={ocupado||eliminar!=="ELIMINAR"} onClick={()=>{if(window.confirm("Tem certeza? Todos os dados serão apagados."))void executar("eliminar",eliminar)}}>Eliminar todas as tabelas</button></article></div></>;
}

const menu = [
  ["dashboard","Dashboard",LayoutDashboard], ["estoque","Estoque",Boxes], ["receitas","Fichas técnicas",ChefHat], ["descoberta","Chat IA",Search], ["explorer","Embeddings",Orbit], ["vendas","Vendas",ShoppingBag], ["perdas","Perdas",AlertTriangle], ["analytics","Analytics SQL",BarChart3], ["dados","CRUD 14 tabelas",Database], ["admin","Administrar banco",Trash2],
] as const;

export default function App() {
  const [pagina,setPagina]=useState<Pagina>("dashboard");
  return <div className="app-shell"><aside><div className="brand"><div><ChefHat size={23}/></div><span>Kitchen<strong>OS</strong></span></div><nav>{menu.map(([id,nome,Icone])=><button key={id} className={pagina===id?"active":""} onClick={()=>setPagina(id)}><Icone size={18}/><span>{nome}</span></button>)}</nav><div className="sidebar-foot"><Users size={17}/><div><strong>Restaurante</strong><small>Ambiente local</small></div></div></aside><main>{pagina==="dashboard"&&<DashboardPage/>}{pagina==="estoque"&&<EstoquePage/>}{pagina==="receitas"&&<ReceitasPage/>}{pagina==="descoberta"&&<ChatAIPage/>}{pagina==="explorer"&&<EmbeddingsPage/>}{pagina==="vendas"&&<TabelaPage titulo="Vendas" subtitulo="Pedidos e valores registrados." endpoint="/pedidos" colunas={[["cod_pedido","Pedido"],["cliente","Cliente"],["forma_pagamento","Pagamento"],["status","Status"],["total","Total"]]}/>} {pagina==="perdas"&&<TabelaPage titulo="Perdas de estoque" subtitulo="Histórico de desperdícios registrados." endpoint="/perdas" colunas={[["data","Data"],["produto","Produto"],["quantidade","Quantidade"],["unidade_medida","Unidade"],["motivo","Motivo"]]}/>} {pagina==="analytics"&&<AnalyticsPage/>}{pagina==="dados"&&<CrudGeralPage/>}{pagina==="admin"&&<AdministracaoPage/>}</main></div>;
}
