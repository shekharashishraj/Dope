var w={};
w['cf8fd32247162']='same mineral';
w['c97e1d10ba477']='human-made';
w['c5100ba62a4ac']='all examples of pure substances';
w['cbd70316afce2']='factor will most affect the speed';
w['cf280c024a6e8']='mostly eats fruit from one particular type of tree';
w['c3592e6450cf0']='convection';
w['cea4b53ba73a4']='best';
w['c608977528e2f']='not a fundamental component';
w['c83eb8d96ad45']='in forests';
w['c66e3d56b4582']='will remain the same';
w['c082c1925975c']='deforestation and land burning for agriculture';
w['c220c7f489d45']='freezing temperature';
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