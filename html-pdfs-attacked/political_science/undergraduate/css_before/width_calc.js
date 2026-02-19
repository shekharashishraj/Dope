var w={};
w['c1d915945b9f9']='oppose the southward expansion of the US';
w['c73b14f7f5cc8']='appellate courts';
w['c1e17f0b64726']='cyber-crime';
w['cd92403bed93f']='in the years following ratification of the Constitution';
w['ccfbf7c8d60c6']='Ways and Means';
w['c36132f5e8f92']='Divided government';
w['caf520b3da337']='Strategic Arms Reduction Treaty';
w['c5b831895cff4']='Delegates';
w['ce0b41a8c0ad8']='unconstitutional';
w['cc7c3381c36bf']='compared to family';
w['c260470edbe2c']='Ideal Policy framework';
w['cb90b96ec0f1d']='postcolonialism and security studies';
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