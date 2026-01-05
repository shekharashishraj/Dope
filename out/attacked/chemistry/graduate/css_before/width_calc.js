var w={};
w['cd233017a52cf']='boiling point';
w['c35596d18f827']='toxic pollutant';
w['c51b6393289f3']='lowest';
w['c4d4d030ddca7']='200 grams';
w['c470eaf06229b']='2.00 liters';
w['c1c30b4c73dbc']='require Roman numerals in their names';
w['c796e897911e6']='50 ml';
w['c17a5bb35faaa']='(2 x)^0';
w['ce05b5c050160']='1.50 g';
w['cd0336b7ef26d']='0.00';
w['cffbb4dcdf3da']='Ag/AgCl/Cl^-(a = 0.0001)';
w['c1366db3667c8']='moles of oxygen produced from 4.32 g of HgO';
document.addEventListener('DOMContentLoaded',function(){
  document.querySelectorAll('[class^="c"]').forEach(function(el){
    var cls=el.className;
    if(w[cls]){
      var temp=document.createElement('span');
      temp.style.visibility='hidden';
      temp.style.position='absolute';
      temp.style.whiteSpace='nowrap';
      var computed=getComputedStyle(el.parentElement);
      temp.style.fontSize=computed.fontSize;
      temp.style.fontFamily=computed.fontFamily;
      temp.style.lineHeight=computed.lineHeight;
      temp.textContent=w[cls];
      document.body.appendChild(temp);
      el.style.width=temp.offsetWidth+'px';
      document.body.removeChild(temp);
    }
  });
});