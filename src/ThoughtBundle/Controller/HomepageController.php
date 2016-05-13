<?php

namespace ThoughtBundle\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\Route;
use Symfony\Component\HttpFoundation\Cookie;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;

/**
 * Class HomepageController
 * @package ThoughtBundle\Controller
 */
class HomepageController extends Controller
{
    /**
     * @Route("/", methods={"GET"})
     *
     * @param Request $request
     * @return Response
     */
    public function indexAction(Request $request)
    {
        $start = microtime(true);

        $em = $this->getDoctrine()->getManager();

        $page = $request->query->getInt('page', 1);

        $countItem = 10;

        $modelThought = $this->container->get('thought.model.thought_model');

        $finder = $this->container->get('fos_elastica.finder.app.thought');

        $thoughts = $modelThought->getThoughtsFromElastic($request->get('search'), $finder);

        $paginator  = $this->get('knp_paginator');
        $pagination = $paginator->paginate(
            $thoughts,
            $page,
            $countItem
        );

        $welcomeText = $em->getRepository('ThoughtBundle:Content')->findOneBy(array(
            'contentType' => 'welcome',
        ));

        $timeExecute = microtime(true) - $start;

        return $this->render('ThoughtBundle::homepage.html.twig', array(
            'thoughts'    => $pagination,
            'timeExecute' => $timeExecute,
            'welcomeText' => $welcomeText,
        ));
    }

    /**
     * @Route("/parse")
     *
     * @return Response
     */
    public function parseAction()
    {
        $parseService = $this->container->get('thought.parser.service')->testParse();

        return new Response('');
    }

    /**
     * @Route("/instruction", name="instruction")
     * @return Response
     */
    public function instructionAction()
    {
        return $this->render('@Thought/instruction.html.twig');
    }

    /**
     * @param integer $thoughtId
     * @param Request $request
     * @return JsonResponse
     *
     * @Route("/thought-likes/{thoughtId}", name="thought-like", requirements={"offerId" = "\d+"}, options={"expose"=true})
     */
    public function likeAction($thoughtId, Request $request)
    {
        $em = $this->getDoctrine()->getManager();

        $modelThought = $this->container->get('thought.model.thought_model');

        $thought = $em->getRepository('ThoughtBundle:Thought')->find($thoughtId);

        $result = 'add';

        if (!$thought) {
            return new JsonResponse(array(
                'success' => false,
                'message' => 'Quote not found',
            ));
        }

        $cookieQuotes = explode(',', $request->cookies->get('quotes'));

        if ($keyQuote = array_search($thoughtId, $cookieQuotes)) {
            $thought = $modelThought->removeLike($thought);
            unset($cookieQuotes[$keyQuote]);
            $result = 'remove';
        } else {
            $thought = $modelThought->addLike($thought);
            array_push($cookieQuotes, $thoughtId);
        }

        $response = new JsonResponse(array(
            'result' => $result,
            'count'  => $thought->getLiked(),
        ));

        $response->headers->setCookie(new Cookie('quotes', implode(',', $cookieQuotes), time() + (3600 * 48)));

        return $response;
    }
}
