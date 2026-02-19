var w={};
w['c2116919947ed']='accepting';
w['c95a0d828783f']='Leo is taller than Cathy';
w['ced7b6a542746']='conducting the souls of dead children to salvation';
w['c826d28d6a6e4']='consequentialist theory';
w['cf3c2f2ab8c61']='does not';
w['c70c27a9bcfc9']='immorality';
w['c2247613b5756']='Successful';
w['c538021f9f1aa']='communal or friendly relationships';
w['cf508427974d9']='586 BCE';
w['ca64d29b69c81']='lack of specific information';
w['c1a3380e44755']='fallacy of accident';
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