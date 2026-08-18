let lang = localStorage.getItem("siteLang") || "en";

function applyLanguage(){
  document.documentElement.lang = lang;

  document.querySelectorAll("[data-en]").forEach(el=>{
    const value = el.getAttribute(lang === "te" ? "data-te" : "data-en");
    if(value !== null) el.textContent = value;
  });

  document.querySelectorAll("[data-placeholder-en]").forEach(el=>{
    el.placeholder = lang === "te" ? el.dataset.placeholderTe : el.dataset.placeholderEn;
  });

  document.querySelectorAll("[data-label-en]").forEach(el=>{
    const value = lang === "te" ? el.dataset.labelTe : el.dataset.labelEn;
    el.textContent = value;
  });

  // Toggle blocks that contain separately written English/Telugu text.
  document.querySelectorAll(".en-text").forEach(el=>el.classList.toggle("d-none", lang === "te"));
  document.querySelectorAll(".te-text").forEach(el=>el.classList.toggle("d-none", lang !== "te"));

  document.querySelectorAll(".lang-btn").forEach(b=>b.textContent = lang === "en" ? "తెలుగు" : "English");
}

function toggleLanguage(){
  lang = lang === "en" ? "te" : "en";
  localStorage.setItem("siteLang", lang);
  applyLanguage();
}

document.addEventListener("DOMContentLoaded", applyLanguage);

function nextStep(n){
  const steps=document.querySelectorAll(".step");
  steps.forEach(s=>s.classList.remove("active"));
  const target=document.querySelector("#step"+n);
  if(target) target.classList.add("active");
  const bar=document.querySelector("#surveyProgress");
  if(bar) bar.style.width=((n/5)*100)+"%";
  window.scrollTo({top:150,behavior:"smooth"});
}
function prevStep(n){nextStep(n)}

function useLocation(){
  if(!navigator.geolocation) return;
  navigator.geolocation.getCurrentPosition(p=>{
    const lat=document.querySelector("#latitude");
    const lng=document.querySelector("#longitude");
    if(lat) lat.value=p.coords.latitude;
    if(lng) lng.value=p.coords.longitude;
    const el=document.querySelector("#locationStatus");
    if(el) el.textContent = lang === "te" ? "మీ ప్రదేశం నమోదు అయింది." : "Location captured.";
  });
}
