<?php

namespace Application\Sonata\UserBundle\Controller;

use Application\Sonata\UserBundle\Form\Type\ChainType;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;
use ThoughtBundle\Entity\Chain;

class ChainController extends Controller
{

    public function navigationAction(Request $request)
    {
        $navigation     = [];
        $navigation[] = [
            'label' => $this->get('translator')->trans('user.chain.list_page.menu_title'),
            'route' => 'sonata_user_chains',
        ];
        $navigation[] = [
            'label' => $this->get('translator')->trans('thought.chain.menu_favorite_chains'),
            'route' => 'sonata_user_favorite_chains',
        ];

        $navigation[] = [
            'label' => $this->get('translator')->trans('thought.chain.public_chains'),
            'route' => 'sonata_user_shared_chains',
        ];
        $navigation[] = [
            'label' => $this->get('translator')->trans('thought.chain.collective_chains'),
            'route' => 'chain_collective',
        ];

        if ($request->get('routeName') == 'chain_page') {

            return $this->render('@ApplicationSonataUser/Profile/menu.html.twig', [
                'menu'             => $navigation,
                'routeName'        => $request->get('routeName'),
            ]);
        }

        return $this->render('@ApplicationSonataUser/Chain/chainNavigation.html.twig', [
            'menu'      => $navigation,
            'routeName' => $request->get('routeName')
            ]
        );
    }

    /**
     * @Route("/chains/favorite", name="sonata_user_favorite_chains")
     * @param Request $request
     * @return Response
     */
    public function favoriteAction(Request $request)
    {
        $em = $this->getDoctrine()->getManager();
        $chains = $em->getRepository('ThoughtBundle:Chain')->getAllFavoriteChains($this->getUser());
        $paginator  = $this->get('knp_paginator');
        $pagination = $paginator->paginate(
            $chains,
            $request->query->getInt('page', 1),
            100
        );
        return $this->render('ApplicationSonataUserBundle:Chain:list.html.twig', array(
            'chains' => $pagination,
        ));
    }

    /**
     * @Route("/chains/changefavorite", name="sonata_user_change_favorite")
     * @param Request $request
     * @return \Symfony\Component\HttpFoundation\RedirectResponse
     */
    public function changeFavoriteAction(Request $request)
    {
        $em    = $this->getDoctrine()->getManager();
        $id    = $request->get('id');
        $chain = $em->getRepository('ThoughtBundle:Chain')->find($id);

        if (!$chain) {
            $this->addFlash('danger', $this->get('translator')->trans('thought.chain.not_exist'));
            return $this->redirect($this->generateUrl('sonata_user_favorite_chains'));
        }

        $favorite = $chain->getFavorite() ? false : true;
        $message  = $favorite ? 'thought.chain.successfully-removed-from-favorites' : 'thought.chain.successfully-added-to-favorites';

        $chain->setFavorite($favorite);

        $em->persist($chain);
        $em->flush();

        $this->addFlash('success', $this->get('translator')->trans($message));

        return $this->redirect($this->generateUrl('sonata_user_favorite_chains'));
    }


    /**
     * @Route("/chains", name="sonata_user_chains")
     * @param Request $request
     * @return Response
     */
    public function listAction(Request $request)
    {
        $em = $this->getDoctrine()->getManager();

        $chains = $em->getRepository('ThoughtBundle:Chain')->findBy(array(
            'user' => $this->getUser(),
        ));

        $paginator  = $this->get('knp_paginator');
        $pagination = $paginator->paginate(
            $chains,
            $request->query->getInt('page', 1),
            100
        );
        return $this->render('ApplicationSonataUserBundle:Chain:list.html.twig', array(
            'chains' => $pagination,
        ));
    }

    /**
     * @Route("/chain/create", name="sonata_user_chain_create")
     *
     * @param Request $request
     * @return Response
     */
    public function createAction(Request $request)
    {
        $chain = new Chain();
        $em = $this->getDoctrine()->getManager();

        $form = $this->createForm(new ChainType(), $chain);
        $form->handleRequest($request);

        if ($request->getMethod() == 'POST') {
            if ($form->isValid()) {
                $chain->setUser($this->getUser());
                $em->persist($chain);
                $em->flush();

                return $this->redirect($this->generateUrl('sonata_user_chains'));
            }
        }

        return $this->render('ApplicationSonataUserBundle:Chain:create.html.twig', array(
            'form' => $form->createView(),
        ));
    }

    /**
     * @Route("/chain/{chainId}/edit", name="sonata_user_chain_edit", requirements={"chainId"="\d+"})
     *
     * @param Request $request
     * @param int     $chainId
     * @return \Symfony\Component\HttpFoundation\RedirectResponse|Response
     */
    public function editAction(Request $request, $chainId)
    {
        $em = $this->getDoctrine()->getManager();

        $chain = $em->getRepository('ThoughtBundle:Chain')->find($chainId);

        if (!$chain) {
            $this->addFlash('success', $this->get('translator')->trans('thought.chain.not_exist'));

            return $this->redirect($this->generateUrl('sonata_user_chains'));
        }

        if (!$this->checkOwner($chain)) {
            $this->addFlash('success', $this->get('translator')->trans('thought.chain.access_denied'));

            return $this->redirect($this->generateUrl('sonata_user_chains'));
        }

        $form = $this->createForm(new ChainType(), $chain);
        $form->handleRequest($request);

        if ($request->getMethod() == 'POST') {
            if ($form->isValid()) {
                $chain->setUser($this->getUser());
                $em->persist($chain);
                $em->flush();

                return $this->redirect($this->generateUrl('sonata_user_chains'));
            }
        }

        return $this->render('ApplicationSonataUserBundle:Chain:edit.html.twig', array(
            'form' => $form->createView(),
        ));
    }

    /**
     * @Route("/chain/{chainId}/remove", name="sonata_user_chain_remove", requirements={"chainId"="\d+"})
     *
     * @param int $chainId
     * @return \Symfony\Component\HttpFoundation\RedirectResponse
     */
    public function removeAction($chainId)
    {
        $em = $this->getDoctrine()->getManager();

        $chain = $em->getRepository('ThoughtBundle:Chain')->find($chainId);

        if (!$chain) {
            $this->addFlash('success', $this->get('translator')->trans('thought.chain.not_exist'));

            return $this->redirect($this->generateUrl('sonata_user_chains'));
        }

        if (!$this->checkOwner($chain)) {
            $this->addFlash('success', $this->get('translator')->trans('thought.chain.access_denied'));

            return $this->redirect($this->generateUrl('sonata_user_chains'));
        }

        $em->remove($chain);
        $em->flush();

        $this->addFlash('success', $this->get('translator')->trans('thought.chain.successfully-remove'));

        return $this->redirect($this->generateUrl('sonata_user_chains'));
    }

    /**
     * @Route("/chain/{chainId}/share", name="sonata_user_chain_share", requirements={"chainId"="\d+"})
     *
     * @param int $chainId
     * @return \Symfony\Component\HttpFoundation\RedirectResponse
     */
    public function shareAction($chainId)
    {
        $em = $this->getDoctrine()->getManager();

        $chain = $em->getRepository('ThoughtBundle:Chain')->find($chainId);

        if (!$chain) {

            $this->addFlash('success', $this->get('translator')->trans('thought.chain.not_exist'));
            return $this->redirect($this->generateUrl('sonata_user_chains'));
        }

        if (!$this->checkOwner($chain)) {

            $this->addFlash('success', $this->get('translator')->trans('thought.chain.access_denied'));
            return $this->redirect($this->generateUrl('sonata_user_chains'));
        }

        $private = $chain->getIsPrivate();

        if ($private == true) {

            $chain->setIsPrivate(false);
        } else {

            $chain->setIsPrivate(true);
            $chain->setIsCollective(false);
        }

        $shareMessage = $private ? 'successfully-shared' : 'successfully-private';

        $em->persist($chain);
        $em->flush();

        $this->addFlash('success', $this->get('translator')->trans('thought.chain.' . $shareMessage));

        return $this->redirect($this->generateUrl('sonata_user_chains'));
    }

    /**
     * @Route("/chain/{chainId}/collective", name="sonata_user_chain_collective", requirements={"chainId"="\d+"})
     * @param int $chainId
     * @return \Symfony\Component\HttpFoundation\RedirectResponse
     */
    public function collectiveAction($chainId)
    {
        $em = $this->getDoctrine()->getManager();
        $chain = $em->getRepository('ThoughtBundle:Chain')->find($chainId);
        if ($chain->getIsPrivate() == false) {

            if (!$this->checkOwner($chain)) {

                $this->addFlash('danger', $this->get('translator')->trans('thought.chain.access_denied'));
                return $this->redirect($this->generateUrl('sonata_user_chains'));
            }

            $collective = $chain->getisCollective();
            $collective = $collective ? false: true;
            $collectiveMessage = $collective ? 'successfully-collectiveded' : 'successfully-personalised';

            $chain->setIsCollective($collective);

            $em->persist($chain);
            $em->flush();
            $this->addFlash('success', $this->get('translator')->trans('thought.chain.' . $collectiveMessage));
        }
        return $this->redirect($this->generateUrl('sonata_user_chains'));
    }

    /**
     * @Route("/chain/collective", name="chain_collective")
     */
    public function listCollectiveAction(Request $request)
    {

        $em = $this->getDoctrine()->getManager();

        $chains = $em->getRepository('ThoughtBundle:Chain')->getAllCollectiveChains();


        $paginator  = $this->get('knp_paginator');
        $pagination = $paginator->paginate(
            $chains,
            $request->query->getInt('page', 1),
            10
        );

        return $this->render('ApplicationSonataUserBundle:Chain:collectiveList.html.twig', array(
            'chains' => $pagination,

        ));
    }

    /**
     * @Route("/shared-chains", name="sonata_user_shared_chains")
     *
     * @param Request $request
     * @return Response
     */
    public function listSharedAction(Request $request)
    {
        $em = $this->getDoctrine()->getManager();

        $chains = $em->getRepository('ThoughtBundle:Chain')->getAllSharedChains();

        $paginator  = $this->get('knp_paginator');
        $pagination = $paginator->paginate(
            $chains,
            $request->query->getInt('page', 1),
            10
        );

        return $this->render('ApplicationSonataUserBundle:Chain:sharedList.html.twig', array(
            'chains' => $pagination,

        ));
    }

    /**
     * @param Request $request
     * @return Response
     */
    public function publicListSharedAction(Request $request)
    {
        $em = $this->getDoctrine()->getManager();

        $chains = $em->getRepository('ThoughtBundle:Chain')->getAllSharedChains();

        $paginator  = $this->get('knp_paginator');
        $pagination = $paginator->paginate(
            $chains,
            $request->query->getInt('page', 1),
            10
        );

        return $this->render('ApplicationSonataUserBundle:Chain:publicSharedList.html.twig', array(
            'chains' => $pagination,
        ));
    }

    /**
     * Check owner chain
     *
     * @param Chain $chain
     * @return bool
     */
    private function checkOwner(Chain $chain)
    {
        return $chain->getUser()->getId() == $this->getUser()->getId() ? true : false;
    }
}
