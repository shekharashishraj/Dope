var w={};
w['cf8fd32247162']='made up entirely of the same mineral';
w['c97e1d10ba477']='human-made';
w['c5100ba62a4ac']='describes all pure substances';
w['cbd70316afce2']='the speed of a sound wave';
w['cf280c024a6e8']='If a virus kills most these trees, which individual lizards will most likely survive?';
w['c3592e6450cf0']='convection';
w['cea4b53ba73a4']='by hand';
w['c608977528e2f']='not a fundamental component';
w['c83eb8d96ad45']='in forests';
w['c66e3d56b4582']='remain the same';
w['c082c1925975c']='deforestation and land burning for agriculture';
w['c220c7f489d45']='freezing temperature of water';
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