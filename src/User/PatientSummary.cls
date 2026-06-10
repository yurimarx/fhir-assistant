Class User.PatientSummary Extends %Persistent
{

Property PatientId As %String;

Property Summary As %String(MAXLEN = "");

Property SummaryVector As %Vector(DATATYPE = "float", LEN = 4096);

/// Índice único para permitir o uso de INSERT OR UPDATE no SQL
Index PatientIdIndex On PatientId [ Unique ];


Storage Default
{
<Data name="PatientSummaryDefaultData">
<Value name="1">
<Value>%%CLASSNAME</Value>
</Value>
<Value name="2">
<Value>PatientId</Value>
</Value>
<Value name="3">
<Value>Summary</Value>
</Value>
<Value name="4">
<Value>SummaryVector</Value>
</Value>
</Data>
<DataLocation>^User.PatientSummaryD</DataLocation>
<DefaultData>PatientSummaryDefaultData</DefaultData>
<IdLocation>^User.PatientSummaryD</IdLocation>
<IndexLocation>^User.PatientSummaryI</IndexLocation>
<StreamLocation>^User.PatientSummaryS</StreamLocation>
<Type>%Storage.Persistent</Type>
}

}
