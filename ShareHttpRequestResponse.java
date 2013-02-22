import burp.*;

public class ShareHttpRequestResponse implements IHttpRequestResponse, IHttpService
{
	protected byte[] request;
	protected byte[] response;
	protected String comment;
	protected String highlight;
	protected String host;
	protected int port;
	protected String protocol;

	public ShareHttpRequestResponse(IHttpRequestResponse original)
	{
		this.request = original.getRequest();
		this.response = original.getResponse();
		this.comment = original.getComment();
		this.highlight = original.getHighlight();
		IHttpService http = original.getHttpService();
		this.host = http.getHost();
		this.port = http.getPort();
		this.protocol = http.getProtocol();
	}
	
	public ShareHttpRequestResponse(byte[] request, byte[] response, String comment, String highlight, String host, int port, String protocol)
	{
		this.request = request;
		this.response = response;
		this.comment = comment;
		this.highlight = highlight;
		this.host = host;
		this.port = port;
		this.protocol = protocol;
	}
    /**
     * This method is used to retrieve the request message.
     *
     * @return The request message.
     */
    public byte[] getRequest()
	{
		return request;
	}

    /**
     * This method is used to update the request message.
     *
     * @param message The new request message.
     */
    public void setRequest(byte[] message)
	{
		this.request = message;
	}

    /**
     * This method is used to retrieve the response message.
     *
     * @return The response message.
     */
    public byte[] getResponse()
	{
		return response;
	}

    /**
     * This method is used to update the response message.
     *
     * @param message The new response message.
     */
    public void setResponse(byte[] message)
	{
		this.response = message;
	}

    /**
     * This method is used to retrieve the user-annotated comment for this item,
     * if applicable.
     *
     * @return The user-annotated comment for this item, or null if none is set.
     */
    public String getComment()
	{
		return comment;
	}

    /**
     * This method is used to update the user-annotated comment for this item.
     *
     * @param comment The comment to be assigned to this item.
     */
    public void setComment(String comment)
	{
		this.comment = comment;
	}

    /**
     * This method is used to retrieve the user-annotated highlight for this
     * item, if applicable.
     *
     * @return The user-annotated highlight for this item, or null if none is
     * set.
     */
    public String getHighlight()
	{
		return highlight;
	}

    /**
     * This method is used to update the user-annotated highlight for this item.
     *
     * @param color The highlight color to be assigned to this item. Accepted
     * values are: red, orange, yellow, green, cyan, blue, pink, magenta, gray,
     * or a null String to clear any existing highlight.
     */
    public void setHighlight(String color)
	{
		this.highlight = color;
	}

    /**
     * This method is used to retrieve the HTTP service for this request /
     * response.
     *
     * @return An
     * <code>IHttpService</code> object containing details of the HTTP service.
     */
    public IHttpService getHttpService()
	{
		return this;
	}

    /**
     * This method is used to update the HTTP service for this request /
     * response.
     *
     * @param httpService An
     * <code>IHttpService</code> object containing details of the new HTTP
     * service.
     */
    public void setHttpService(IHttpService httpService)
	{
		host = httpService.getHost();
		port = httpService.getPort();
		protocol = httpService.getProtocol();
	}

    /**
     * This method returns the hostname or IP address for the service.
     *
     * @return The hostname or IP address for the service.
     */
    public String getHost()
	{
		return host;
	}

    /**
     * This method returns the port number for the service.
     *
     * @return The port number for the service.
     */
    public int getPort()
	{
		return port;
	}

    /**
     * This method returns the protocol for the service.
     *
     * @return The protocol for the service. Expected values are "http" or
     * "https".
     */
    public String getProtocol()
	{
		return protocol;
	}
}