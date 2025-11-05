document.getElementById("calcularRefino").addEventListener("click", function() {
  const grau = document.getElementById("grau").value;
  const quantidade = parseInt(document.getElementById("quantidade").value, 10);
  const resultado = calcularRefino(grau, quantidade);
  if (resultado.erro) {
    alert(resultado.erro);
    return;
  }
  document.getElementById("qtdG2").textContent = resultado.consumos.R2;
  document.getElementById("qtdG3").textContent = resultado.consumos.R3;
  document.getElementById("qtdG4").textContent = resultado.consumos.R4;
  document.getElementById("qtdG5").textContent = resultado.consumos.R5;
  document.getElementById("qtdBarras").textContent = resultado.barras.barras;
});


function calcularRefino(grau, quantidade) {
  const regras = { G5: 3, G4: 2, G3: 2, G2: 1 };
  if (!regras[grau]) return { erro: "Selecione G2, G3, G4 ou G5" };

  let barras, consumos = { R2: 0, R3: 0, R4: 0, R5: 0 };

  if (grau === "G2") {
    consumos.R2 = quantidade;
    barras = quantidade;
  } else {
    const consumo = regras[grau];
    barras = quantidade / consumo;
    consumos[grau.replace("G", "R")] = quantidade;
    consumos.R2 = barras;
  }

  if (grau !== "G2") {
    consumos.R3 = barras * regras.G3;
    consumos.R4 = barras * regras.G4;
    consumos.R5 = barras * regras.G5;
  } else {
    consumos.R3 = quantidade / regras.G3;
    consumos.R4 = quantidade / regras.G4;
    consumos.R5 = quantidade / regras.G5;
  }

  return {
    tipo: `Cálculo a partir do ${grau}`,
    barras: { barras },
    consumos
  };
}

console.log(calcularRefino("G4", 300));
